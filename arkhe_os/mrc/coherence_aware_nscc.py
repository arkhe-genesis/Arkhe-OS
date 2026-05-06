# arkhe_os/mrc/coherence_aware_nscc.py
"""
Extensão do algoritmo NSCC (UltraEthernet) com métricas de coerência em tempo real.
Ajusta congestion window baseado em Φ_C de caminho além de ECN e RTT.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import time

class CongestionSignal(Enum):
    NONE = 0
    ECN_MARKED = 1
    TRIMMED = 2
    COHERENCE_LOW = 3
    PATH_UNRELIABLE = 4

@dataclass
class PathCoherenceMetrics:
    """Métricas de coerência para um caminho específico."""
    path_id: str                    # Identificador único do caminho (EV + plane)
    coherence_current: float        # Φ_C atual medido
    coherence_history: List[float]  # Histórico recente de Φ_C
    rtt_current: float              # RTT atual em ms
    rtt_baseline: float             # RTT baseline sem congestão
    packet_loss_rate: float         # Taxa de perda estimada
    last_updated: float             # Timestamp da última atualização

    def coherence_trend(self, window: int = 10) -> float:
        """Calcula tendência de coerência (derivada aproximada)."""
        if len(self.coherence_history) < window:
            return 0.0
        recent = self.coherence_history[-window:]
        return (recent[-1] - recent[0]) / max(1, len(recent) - 1)

    def is_congested(
        self,
        coherence_threshold: float = 0.7,
        rtt_threshold: float = 2.0,  # 2x baseline
    ) -> bool:
        """Verifica se caminho está congestionado baseado em múltiplos sinais."""
        if self.coherence_current < coherence_threshold:
            return True
        if self.rtt_current > rtt_threshold * self.rtt_baseline:
            return True
        if self.packet_loss_rate > 0.05:  # 5% loss
            return True
        return False

@dataclass
class QPCCoherenceState:
    """Estado de coerência por Queue Pair para controle de congestão."""
    qp_id: str
    target_coherence: float = 0.85      # Φ_C alvo para operação ideal
    lambda_adjust: float = 0.3          # Peso do ajuste baseado em coerência
    cwnd: float = 10.0                  # Congestion window inicial (em pacotes)
    cwnd_min: float = 2.0               # Window mínima
    cwnd_max: float = 1000.0            # Window máxima
    inflight: int = 0                   # Pacotes em trânsito
    path_metrics: Dict[str, PathCoherenceMetrics] = field(default_factory=dict)
    last_adjustment_time: float = 0.0
    adjustment_cooldown: float = 0.1    # 100ms entre ajustes

    def get_path_coherence(self, path_id: str) -> Optional[float]:
        """Obtém coerência atual para um caminho específico."""
        if path_id in self.path_metrics:
            return self.path_metrics[path_id].coherence_current
        return None

    def update_path_metrics(
        self,
        path_id: str,
        coherence: float,
        rtt: float,
        loss_rate: float,
        rtt_baseline: Optional[float] = None,
    ):
        """Atualiza métricas de coerência para um caminho."""
        if path_id not in self.path_metrics:
            self.path_metrics[path_id] = PathCoherenceMetrics(
                path_id=path_id,
                coherence_current=coherence,
                coherence_history=[coherence],
                rtt_current=rtt,
                rtt_baseline=rtt_baseline or rtt,
                packet_loss_rate=loss_rate,
                last_updated=time.time(),
            )
        else:
            metrics = self.path_metrics[path_id]
            metrics.coherence_current = coherence
            metrics.coherence_history.append(coherence)
            # Manter histórico limitado
            if len(metrics.coherence_history) > 100:
                metrics.coherence_history = metrics.coherence_history[-100:]
            metrics.rtt_current = rtt
            metrics.packet_loss_rate = loss_rate
            metrics.last_updated = time.time()
            if rtt_baseline:
                metrics.rtt_baseline = rtt_baseline

class CoherenceAwareNSCC:
    """
    Controlador de congestão NSCC estendido com métricas de coerência.

    Baseado no algoritmo UltraEthernet NSCC [UESPEC Sec. 3.6.13], com extensões:
    - Ajuste de cwnd baseado em Φ_C de caminho
    - Agregação de sinais de congestão (ECN, trimming, coerência)
    - Adaptação dinâmica de parâmetros baseada em histórico
    """

    def __init__(
        self,
        qp_id: str,
        target_qdelay: float = 1.0,      # Target queueing delay em ms
        alpha: float = 0.1,              # Incremento proporcional
        beta: float = 0.5,               # Decremento multiplicativo
        coherence_lambda: float = 0.3,   # Peso do ajuste por coerência
        min_coherence: float = 0.6,      # Φ_C mínimo para operação normal
    ):
        self.state = QPCCoherenceState(
            qp_id=qp_id,
            target_coherence=min_coherence + 0.15,  # Target > min
            lambda_adjust=coherence_lambda,
        )
        self.target_qdelay = target_qdelay
        self.alpha = alpha
        self.beta = beta
        self.min_coherence = min_coherence

        # Estatísticas para monitoramento
        self.stats = {
            'adjustments': 0,
            'coherence_triggers': 0,
            'ecn_triggers': 0,
            'trim_triggers': 0,
        }

    def on_ack(
        self,
        path_id: str,
        newly_acked_bytes: int,
        rtt_sample: float,
        ecn_marked: bool,
        coherence_sample: float,
        timestamp: float,
    ) -> Dict:
        """
        Processa ACK recebido e ajusta congestion window.

        Implementa lógica NSCC estendida com coerência:
        1. Atualizar métricas do caminho
        2. Calcular sinais de congestão agregados
        3. Ajustar cwnd baseado em combinação de sinais
        4. Aplicar cooldown para evitar oscilações
        """
        # Atualizar métricas do caminho
        self.state.update_path_metrics(
            path_id=path_id,
            coherence=coherence_sample,
            rtt=rtt_sample,
            loss_rate=0.0,  # ACK indica sucesso
            rtt_baseline=self.state.path_metrics.get(path_id, PathCoherenceMetrics(path_id, 0, [], 0, 0, 0, 0)).rtt_baseline,
        )

        # Calcular sinais de congestão
        signals = self._compute_congestion_signals(
            path_id=path_id,
            ecn_marked=ecn_marked,
            coherence=coherence_sample,
            rtt=rtt_sample,
        )

        # Verificar cooldown
        if timestamp - self.state.last_adjustment_time < self.state.adjustment_cooldown:
            return {'adjusted': False, 'reason': 'cooldown', 'cwnd': self.state.cwnd}

        # Calcular ajuste de cwnd
        old_cwnd = self.state.cwnd
        new_cwnd = self._compute_cwnd_adjustment(old_cwnd, signals, newly_acked_bytes)

        # Aplicar limites
        new_cwnd = max(self.state.cwnd_min, min(self.state.cwnd_max, new_cwnd))

        # Atualizar estado
        self.state.cwnd = new_cwnd
        self.state.last_adjustment_time = timestamp
        self.state.inflight = max(0, self.state.inflight - newly_acked_bytes)
        self.stats['adjustments'] += 1

        # Registrar triggers para estatísticas
        if signals['coherence_low']:
            self.stats['coherence_triggers'] += 1
        if signals['ecn_marked']:
            self.stats['ecn_triggers'] += 1

        return {
            'adjusted': True,
            'old_cwnd': round(old_cwnd, 2),
            'new_cwnd': round(new_cwnd, 2),
            'signals': signals,
            'path_coherence': coherence_sample,
        }

    def on_nack(
        self,
        path_id: str,
        nack_reason: str,
        coherence_sample: float,
        timestamp: float,
    ) -> Dict:
        """Processa NACK recebido (perda detectada)."""
        # Atualizar métricas com perda
        self.state.update_path_metrics(
            path_id=path_id,
            coherence=coherence_sample,
            rtt=0,  # NACK não fornece RTT confiável
            loss_rate=1.0,  # Perda confirmada
        )

        # NACK sempre indica problema: reduzir cwnd agressivamente
        old_cwnd = self.state.cwnd
        # Redução multiplicativa mais forte para trimming
        if 'TRIM' in nack_reason:
            self.stats['trim_triggers'] += 1
            new_cwnd = old_cwnd * (1 - self.beta * 1.5)  # 1.5x mais agressivo
        else:
            new_cwnd = old_cwnd * (1 - self.beta)

        new_cwnd = max(self.state.cwnd_min, new_cwnd)
        self.state.cwnd = new_cwnd
        self.state.last_adjustment_time = timestamp

        return {
            'adjusted': True,
            'old_cwnd': round(old_cwnd, 2),
            'new_cwnd': round(new_cwnd, 2),
            'nack_reason': nack_reason,
            'path_coherence': coherence_sample,
        }

    def on_new_data(self, nominal_pktsize: int) -> bool:
        """
        Verifica se pode enviar novo dado baseado em cwnd e inflight.

        Returns:
            True se há espaço no window para enviar
        """
        available = self.state.cwnd - self.state.inflight
        return available >= nominal_pktsize

    def on_send(self, nominal_pktsize: int, path_id: str):
        """Notifica que pacote foi enviado (para tracking de inflight)."""
        self.state.inflight += nominal_pktsize
        # Atualizar métricas do caminho com envio
        if path_id in self.state.path_metrics:
            self.state.path_metrics[path_id].last_updated = time.time()

    def _compute_congestion_signals(
        self,
        path_id: str,
        ecn_marked: bool,
        coherence: float,
        rtt: float,
    ) -> Dict[str, bool]:
        """Calcula sinais de congestão agregados de múltiplas fontes."""
        metrics = self.state.path_metrics.get(path_id)

        signals = {
            'ecn_marked': ecn_marked,
            'coherence_low': coherence < self.min_coherence,
            'coherence_declining': False,
            'rtt_high': False,
            'path_unreliable': False,
        }

        if metrics:
            # Verificar tendência de coerência
            trend = metrics.coherence_trend(window=5)
            signals['coherence_declining'] = trend < -0.02  # Queda > 2%/sample

            # Verificar RTT relativo ao baseline
            if metrics.rtt_baseline > 0:
                signals['rtt_high'] = rtt > 2.0 * metrics.rtt_baseline

            # Caminho não confiável se múltiplos sinais negativos
            negative_signals = sum([
                signals['ecn_marked'],
                signals['coherence_low'],
                signals['coherence_declining'],
                signals['rtt_high'],
                metrics.packet_loss_rate > 0.02,
            ])
            signals['path_unreliable'] = negative_signals >= 3

        return signals

    def _compute_cwnd_adjustment(
        self,
        current_cwnd: float,
        signals: Dict[str, bool],
        newly_acked_bytes: int,
    ) -> float:
        """
        Calcula novo valor de cwnd baseado em sinais agregados.

        Lógica de ajuste:
        - ECN marcado + RTT alto: decremento multiplicativo (β)
        - Coerência baixa: ajuste suave baseado em λ(Φ_C - Φ_target)
        - Sem sinais negativos: incremento proporcional (α)
        - Combinação de sinais: priorizar sinal mais severo
        """
        # Fator base do NSCC original
        if signals['ecn_marked'] and signals['rtt_high']:
            # Congestão confirmada: reduzir agressivamente
            base_factor = 1 - self.beta
        elif signals['ecn_marked'] or signals['rtt_high']:
            # Sinal único: reduzir moderadamente
            base_factor = 1 - self.beta * 0.5
        else:
            # Sem ECN/RTT alto: incrementar proporcionalmente
            base_factor = 1 + self.alpha * (newly_acked_bytes / max(1, current_cwnd * 1400))

        # Fator de ajuste por coerência
        avg_coherence = np.mean([
            m.coherence_current
            for m in self.state.path_metrics.values()
        ]) if self.state.path_metrics else self.state.target_coherence

        coherence_factor = 1 + self.state.lambda_adjust * (
            avg_coherence - self.state.target_coherence
        )
        # Limitar fator de coerência para evitar oscilações
        coherence_factor = max(0.8, min(1.2, coherence_factor))

        # Combinar fatores
        new_cwnd = current_cwnd * base_factor * coherence_factor

        # Ajuste adicional se caminho específico está com coerência muito baixa
        for path_id, metrics in self.state.path_metrics.items():
            if metrics.coherence_current < self.min_coherence - 0.1:
                # Reduzir adicionalmente para caminhos problemáticos
                new_cwnd *= 0.95  # 5% redução extra por caminho ruim

        return new_cwnd

    def get_state_summary(self) -> Dict:
        """Retorna resumo do estado para monitoramento."""
        path_summaries = {}
        for path_id, metrics in self.state.path_metrics.items():
            path_summaries[path_id] = {
                'coherence': round(metrics.coherence_current, 4),
                'rtt_ms': round(metrics.rtt_current, 2),
                'rtt_baseline_ms': round(metrics.rtt_baseline, 2),
                'loss_rate': round(metrics.packet_loss_rate, 4),
                'trend': round(metrics.coherence_trend(), 4),
            }

        return {
            'qp_id': self.state.qp_id,
            'cwnd': round(self.state.cwnd, 2),
            'inflight': self.state.inflight,
            'target_coherence': self.state.target_coherence,
            'avg_path_coherence': round(
                np.mean([m.coherence_current for m in self.state.path_metrics.values()])
                if self.state.path_metrics else 0, 4
            ),
            'paths': path_summaries,
            'stats': self.stats,
        }
