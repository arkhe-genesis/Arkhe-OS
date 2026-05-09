# arkhe_os/mrc/active_path_prober.py
"""
Sistema de sondagem ativa de caminhos usando EV probes para medição
de path health, latência e disponibilidade em tempo real.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
import time
import random
from collections import defaultdict, deque

class ProbeResult(Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    PATH_UNREACHABLE = "path_unreachable"
    COHERENCE_TOO_LOW = "coherence_too_low"
    ERROR = "error"

@dataclass
class ProbeRequest:
    """Solicitação de probe ativo."""
    probe_id: str
    dest_node: str
    path_id: str           # EV + plane identifier
    entropy_value: int     # EV específico para este caminho
    payload_size: int      # Tamanho do payload do probe
    timeout_ms: float      # Timeout para resposta
    priority: int = 0      # Prioridade (0=normal, 1=alta, 2=crítica)
    metadata: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

@dataclass
class ProbeResponse:
    """Resposta de probe ativo."""
    probe_id: str
    result: ProbeResult
    rtt_ms: float                    # Round-trip time medido
    coherence_measured: float        # Φ_C medido no caminho de volta
    path_health_score: float         # Score agregado de saúde [0, 1]
    error_details: Optional[str] = None
    received_at: float = field(default_factory=time.time)

    def compute_path_health(
        self,
        rtt_baseline: float,
        coherence_target: float = 0.85,
        weights: Dict[str, float] = None,
    ) -> float:
        """
        Calcula score de saúde do caminho baseado em múltiplas métricas.

        Fórmula: H = w_rtt * (1 - normalized_rtt) + w_coh * coherence + w_loss * (1 - loss)
        """
        if weights is None:
            weights = {'rtt': 0.4, 'coherence': 0.4, 'loss': 0.2}

        # Normalizar RTT: 1.0 se baseline, 0.0 se 3x baseline
        rtt_score = max(0, 1 - (self.rtt_ms - rtt_baseline) / (2 * rtt_baseline))

        # Score de coerência já está em [0, 1]
        coh_score = self.coherence_measured

        # Estimativa de perda baseada em resultado
        loss_score = 1.0 if self.result == ProbeResult.SUCCESS else 0.0

        return (
            weights['rtt'] * rtt_score +
            weights['coherence'] * coh_score +
            weights['loss'] * loss_score
        )

@dataclass
class PathHealthSummary:
    """Resumo agregado de saúde para um caminho."""
    path_id: str
    health_score: float              # Score atual [0, 1]
    health_trend: float              # Tendência (derivada)
    avg_rtt_ms: float
    avg_coherence: float
    success_rate: float              # % de probes bem-sucedidos
    last_probe_time: float
    probe_count: int
    confidence: float                # Confiança na estimativa [0, 1]

class ActivePathProber:
    """
    Sistema de sondagem ativa para medição de health de caminhos.

    Funcionalidades:
    - Agendamento adaptativo de probes baseado em criticidade
    - Agregação de métricas com janelas temporais
    - Detecção de degradação proativa
    - Integração com EV selection para load balancing
    """

    def __init__(
        self,
        node_id: str,
        probe_interval_base: float = 1.0,      # Intervalo base entre probes (s)
        min_probes_per_path: int = 3,           # Mínimo de probes para estimativa confiável
        health_decay_rate: float = 0.95,        # Decaimento de health score sem updates
        coherence_threshold: float = 0.7,       # Φ_C mínimo para considerar caminho saudável
    ):
        self.node_id = node_id
        self.probe_interval_base = probe_interval_base
        self.min_probes = min_probes_per_path
        self.health_decay = health_decay_rate
        self.min_coherence = coherence_threshold

        # Estado interno
        self.pending_probes: Dict[str, ProbeRequest] = {}
        self.probe_results: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=50)  # Manter últimos 50 resultados por caminho
        )
        self.path_health: Dict[str, PathHealthSummary] = {}
        self.probe_scheduler: Dict[str, float] = {}  # Próximo probe permitido por caminho

        # Callbacks para integração
        self.on_probe_result: Optional[Callable] = None
        self.on_path_degraded: Optional[Callable] = None

        # Estatísticas
        self.stats = {
            'probes_sent': 0,
            'probes_received': 0,
            'timeouts': 0,
            'avg_rtt_ms': 0.0,
        }

    def schedule_probe(
        self,
        dest_node: str,
        path_id: str,
        entropy_value: int,
        priority: int = 0,
        payload_size: int = 64,  # Pequeno para minimizar overhead
        timeout_ms: float = 100.0,
    ) -> str:
        """
        Agenda probe ativo para um caminho específico.

        Returns:
            probe_id único para correlacionar request/response
        """
        # Verificar rate limiting por caminho
        now = time.time()
        if path_id in self.probe_scheduler:
            if now < self.probe_scheduler[path_id]:
                # Agendamento muito frequente: aumentar intervalo
                return ""  # Indicar que probe foi throttled

        # Gerar ID único
        probe_id = f"{self.node_id}_{int(now * 1000)}_{random.randint(0, 9999)}"

        # Criar request
        request = ProbeRequest(
            probe_id=probe_id,
            dest_node=dest_node,
            path_id=path_id,
            entropy_value=entropy_value,
            payload_size=payload_size,
            timeout_ms=timeout_ms,
            priority=priority,
            metadata={'scheduler_priority': priority},
        )

        # Armazenar pending
        self.pending_probes[probe_id] = request
        self.stats['probes_sent'] += 1

        # Atualizar scheduler (intervalo adaptativo baseado em prioridade)
        interval = self.probe_interval_base / (priority + 1)
        self.probe_scheduler[path_id] = now + interval

        # Em produção: enviar probe via MRC transport
        # self._send_probe_packet(request)

        return probe_id

    def process_probe_response(
        self,
        response: ProbeResponse,
        rtt_baseline: float,
    ) -> PathHealthSummary:
        """
        Processa resposta de probe e atualiza saúde do caminho.

        Args:
            response: Resposta recebida do probe
            rtt_baseline: RTT baseline para normalização

        Returns:
            PathHealthSummary atualizado
        """
        # Remover do pending
        if response.probe_id in self.pending_probes:
            del self.pending_probes[response.probe_id]

        self.stats['probes_received'] += 1
        self.stats['avg_rtt_ms'] = (
            0.99 * self.stats['avg_rtt_ms'] + 0.01 * response.rtt_ms
        )

        # Calcular path health score
        health_score = response.compute_path_health(
            rtt_baseline=rtt_baseline,
            coherence_target=self.min_coherence + 0.15,
        )

        # Adicionar ao histórico do caminho
        path_id = self.pending_probes.get(response.probe_id, ProbeRequest("", "", "", 0, 0, 0)).path_id if response.probe_id in self.pending_probes else "unknown"
        self.probe_results[path_id].append(response)

        # Atualizar ou criar resumo de saúde
        summary = self._update_path_health_summary(
            path_id=path_id,
            health_score=health_score,
            response=response,
        )

        # Verificar degradação e notificar callbacks
        if summary.health_score < 0.5 and summary.confidence > 0.8:
            if self.on_path_degraded:
                self.on_path_degraded(path_id, summary)

        # Notificar callback de resultado
        if self.on_probe_result:
            self.on_probe_result(response, summary)

        return summary

    def get_path_health(self, path_id: str) -> Optional[PathHealthSummary]:
        """Obtém resumo de saúde atual para um caminho."""
        # Atualizar com decaimento se não há updates recentes
        if path_id in self.path_health:
            summary = self.path_health[path_id]
            time_since_update = time.time() - summary.last_probe_time
            if time_since_update > 5.0:  # 5 segundos sem update
                # Aplicar decaimento exponencial
                decay = self.health_decay ** (time_since_update / 5.0)
                summary.health_score = max(0, summary.health_score * decay)
                summary.confidence = max(0, summary.confidence * decay * 1.1)
        return self.path_health.get(path_id)

    def get_recommended_paths(
        self,
        dest_node: str,
        min_health: float = 0.6,
        max_paths: int = 4,
    ) -> List[Tuple[str, float]]:
        """
        Retorna caminhos recomendados para um destino baseado em health.

        Returns:
            Lista de (path_id, health_score) ordenada por saúde decrescente
        """
        candidates = []
        for path_id, summary in self.path_health.items():
            if dest_node in path_id and summary.health_score >= min_health:
                # Weight by both health and confidence
                weighted_score = summary.health_score * summary.confidence
                candidates.append((path_id, weighted_score))

        # Ordenar e retornar top-N
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:max_paths]

    def _update_path_health_summary(
        self,
        path_id: str,
        health_score: float,
        response: ProbeResponse,
    ) -> PathHealthSummary:
        """Atualiza ou cria resumo de saúde para um caminho."""
        results = self.probe_results[path_id]

        # Calcular métricas agregadas
        successful = [r for r in results if r.result == ProbeResult.SUCCESS]
        success_rate = len(successful) / max(1, len(results))

        avg_rtt = np.mean([r.rtt_ms for r in successful]) if successful else response.rtt_ms
        avg_coh = np.mean([r.coherence_measured for r in successful]) if successful else response.coherence_measured

        # Calcular tendência (regressão linear simples)
        if len(results) >= 5:
            health_values = [r.compute_path_health(10.0) for r in list(results)[-10:]]  # rtt_baseline placeholder
            trend = np.polyfit(range(len(health_values)), health_values, 1)[0]
        else:
            trend = 0.0

        # Calcular confiança baseada em número de probes e consistência
        n_probes = len(results)
        confidence = min(1.0, n_probes / self.min_probes)
        if n_probes >= 10:
            # Reduzir confiança se alta variância
            health_std = np.std([r.compute_path_health(10.0) for r in results[-20:]])
            confidence *= max(0.5, 1 - health_std)

        # Criar ou atualizar summary
        if path_id not in self.path_health:
            summary = PathHealthSummary(
                path_id=path_id,
                health_score=health_score,
                health_trend=trend,
                avg_rtt_ms=avg_rtt,
                avg_coherence=avg_coh,
                success_rate=success_rate,
                last_probe_time=response.received_at,
                probe_count=n_probes,
                confidence=confidence,
            )
        else:
            summary = self.path_health[path_id]
            # Smooth update para evitar oscilações
            alpha = 0.3 if n_probes < 10 else 0.1
            summary.health_score = (1 - alpha) * summary.health_score + alpha * health_score
            summary.health_trend = trend
            summary.avg_rtt_ms = (1 - alpha) * summary.avg_rtt_ms + alpha * avg_rtt
            summary.avg_coherence = (1 - alpha) * summary.avg_coherence + alpha * avg_coh
            summary.success_rate = success_rate
            summary.last_probe_time = response.received_at
            summary.probe_count = n_probes
            summary.confidence = confidence

        self.path_health[path_id] = summary
        return summary

    def get_prober_stats(self) -> Dict:
        """Retorna estatísticas do prober para monitoramento."""
        return {
            **self.stats,
            'pending_probes': len(self.pending_probes),
            'paths_monitored': len(self.path_health),
            'avg_health_score': round(
                np.mean([s.health_score for s in self.path_health.values()])
                if self.path_health else 0, 4
            ),
        }
