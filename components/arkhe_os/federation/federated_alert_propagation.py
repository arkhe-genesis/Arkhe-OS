#!/usr/bin/env python3
"""
federated_alert_propagation.py — Propagação de alertas críticos
através da federação de observatórios com roteamento adaptativo.
"""

import asyncio
import time
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import deque
import logging
import numpy as np

class AlertSeverity(Enum):
    """Níveis de severidade para alertas federados."""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"
    COSMIC_EMERGENCY = "cosmic_emergency"  # Degradação cósmica crítica

class AlertPropagationMode(Enum):
    """Modos de propagação de alertas."""
    FLOOD = auto()           # Broadcast para todos os nós
    TARGETED = auto()        # Enviar apenas para nós relevantes
    HIERARCHICAL = auto()    # Propagar via hierarquia de confiança
    ADAPTIVE = auto()        # Modo adaptativo baseado em severidade e contexto

@dataclass
class FederatedAlert:
    """Alerta crítico propagado através da federação."""
    alert_id: str
    alert_type: str  # 'security_anomaly', 'cosmic_degradation', 'consensus_failure', etc.
    severity: AlertSeverity
    source_node_id: str
    description: str
    affected_metrics: List[str]
    timestamp: float
    propagation_mode: AlertPropagationMode = AlertPropagationMode.ADAPTIVE
    ttl_hops: int = 5  # Número máximo de hops de propagação
    priority_score: float = 1.0  # Score de prioridade para roteamento
    signature: str = ''  # Assinatura criptográfica
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'severity': self.severity.value,
            'source_node_id': self.source_node_id,
            'description': self.description,
            'affected_metrics': self.affected_metrics,
            'timestamp': self.timestamp,
            'propagation_mode': self.propagation_mode.name,
            'ttl_hops': self.ttl_hops,
            'priority_score': self.priority_score,
            'signature': self.signature,
            'metadata': self.metadata
        }

    def compute_priority_score(self) -> float:
        """Computa score de prioridade para roteamento adaptativo."""
        # Fatores de prioridade
        severity_weights = {
            AlertSeverity.INFO: 0.1,
            AlertSeverity.WARNING: 0.3,
            AlertSeverity.HIGH: 0.7,
            AlertSeverity.CRITICAL: 1.0,
            AlertSeverity.COSMIC_EMERGENCY: 2.0
        }

        base_score = severity_weights.get(self.severity, 0.5)

        # Fatores adicionais
        if 'cosmic' in self.alert_type.lower():
            base_score *= 1.3  # Alertas cósmicos têm prioridade extra
        if len(self.affected_metrics) > 3:
            base_score *= 1.2  # Múltiplas métricas afetadas
        if self.metadata.get('mission_critical', False):
            base_score *= 1.5  # Missão crítica

        return min(2.0, base_score)  # Limitar a 2.0

class FederatedAlertPropagation:
    """
    Sistema de propagação de alertas através da federação de observatórios.
    Implementa roteamento adaptativo baseado em severidade, criticidade e topologia.
    """

    def __init__(
        self,
        node_id: str,
        federation_config: Dict[str, Any],
        known_observatories: Dict[str, Any],
        key_manager: Optional['KeyManager'] = None
    ):
        self.node_id = node_id
        self.config = federation_config
        self.known_observatories = known_observatories
        self.key_manager = key_manager

        # Alertas processados (para evitar duplicação)
        self.processed_alerts: Set[str] = set()
        self.alert_history: deque = deque(maxlen=1000)

        # Fila de alertas para propagação
        self.propagation_queue: asyncio.Queue = asyncio.Queue()

        # Estado de propagação
        self.propagation_stats = {
            'alerts_received': 0,
            'alerts_propagated': 0,
            'alerts_deduplicated': 0,
            'avg_propagation_latency_ms': 0.0
        }

        # Callbacks para notificação de alertas
        self.alert_callbacks: List[Callable] = []

        # Thread de propagação
        self._propagation_task: Optional[asyncio.Task] = None

        logging.info(f"✅ FederatedAlertPropagation initialized: node={node_id}")

    async def create_and_propagate_alert(
        self,
        alert_type: str,
        severity: AlertSeverity,
        description: str,
        affected_metrics: List[str],
        metadata: Optional[Dict] = None,
        propagation_mode: Optional[AlertPropagationMode] = None
    ) -> FederatedAlert:
        """
        Cria novo alerta e inicia propagação federada.

        Returns:
            FederatedAlert criado
        """
        # Criar alerta
        alert = FederatedAlert(
            alert_id=hashlib.sha256(
                f"{alert_type}:{description}:{time.time()}".encode()
            ).hexdigest()[:16],
            alert_type=alert_type,
            severity=severity,
            source_node_id=self.node_id,
            description=description,
            affected_metrics=affected_metrics,
            timestamp=time.time(),
            propagation_mode=propagation_mode or AlertPropagationMode.ADAPTIVE,
            ttl_hops=5,
            priority_score=1.0,  # Será computado abaixo
            signature='',
            metadata=metadata or {}
        )

        # Computar score de prioridade
        alert.priority_score = alert.compute_priority_score()

        # Assinar alerta
        if self.key_manager:
            alert.signature = self.key_manager.sign_content(
                json.dumps(alert.to_dict(), sort_keys=True)
            )

        # Processar alerta localmente primeiro
        await self._process_alert_locally(alert)

        # Iniciar propagação
        await self.propagation_queue.put(alert)

        # Iniciar task de propagação se não estiver rodando
        if not self._propagation_task or self._propagation_task.done():
            self._propagation_task = asyncio.create_task(self._propagation_loop())

        logging.info(f"🚨 Alert created and queued for propagation: {alert.alert_id} ({severity.value})")
        return alert

    async def _propagation_loop(self):
        """Loop principal de propagação de alertas."""
        while True:
            try:
                alert = await self.propagation_queue.get()

                # Determinar nós alvo para propagação
                target_nodes = await self._select_propagation_targets(alert)

                # Propagar para cada nó alvo
                propagation_tasks = [
                    self._propagate_to_node(alert, target_node)
                    for target_node in target_nodes
                ]

                if propagation_tasks:
                    results = await asyncio.gather(*propagation_tasks, return_exceptions=True)

                    # Atualizar estatísticas
                    successful = sum(1 for r in results if isinstance(r, bool) and r)
                    self.propagation_stats['alerts_propagated'] += successful

                self.propagation_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"⚠️ Propagation loop error: {e}")
                await asyncio.sleep(1.0)  # Evitar busy loop em erro

    async def _select_propagation_targets(
        self,
        alert: FederatedAlert
    ) -> List[str]:
        """Seleciona nós alvo para propagação baseado no modo e prioridade."""
        if alert.propagation_mode == AlertPropagationMode.FLOOD:
            # Broadcast para todos os validadores
            return [
                nid for nid, obs in self.known_observatories.items()
                if obs.get('federation_role') == 'validator' and nid != self.node_id
            ]

        elif alert.propagation_mode == AlertPropagationMode.TARGETED:
            # Enviar apenas para nós com métricas afetadas
            targets = []
            for nid, obs in self.known_observatories.items():
                if nid == self.node_id:
                    continue
                # Verificar se nó monitora métricas afetadas
                node_capabilities = obs.get('capabilities', {})
                supported_metrics = node_capabilities.get('supported_metrics', [])
                if any(metric in supported_metrics for metric in alert.affected_metrics):
                    targets.append(nid)
            return targets

        elif alert.propagation_mode == AlertPropagationMode.HIERARCHICAL:
            # Propagar via hierarquia de confiança
            # (simplificação: priorizar nós com alta confiança)
            trusted_nodes = [
                nid for nid, obs in self.known_observatories.items()
                if nid != self.node_id and obs.get('trust_score', 0) > 0.8
            ]
            return trusted_nodes[:3]  # Limitar a 3 nós de alta confiança

        else:  # ADAPTIVE
            # Seleção adaptativa baseada em severidade e criticidade
            if alert.severity == AlertSeverity.COSMIC_EMERGENCY:
                # Emergência cósmica: propagar para todos imediatamente
                return [
                    nid for nid in self.known_observatories
                    if nid != self.node_id
                ]
            elif alert.priority_score > 1.5:
                # Alta prioridade: propagar para validadores + observadores críticos
                return [
                    nid for nid, obs in self.known_observatories.items()
                    if nid != self.node_id and (
                        obs.get('federation_role') == 'validator' or
                        obs.get('capabilities', {}).get('mission_critical', False)
                    )
                ]
            else:
                # Prioridade normal: propagar apenas para validadores próximos
                # (simplificação: aleatório com viés para alta confiança)
                candidates = [
                    nid for nid, obs in self.known_observatories.items()
                    if nid != self.node_id and obs.get('federation_role') == 'validator'
                ]
                # Amostrar com peso baseado em trust_score
                weights = [
                    self.known_observatories[nid].get('trust_score', 0.5)
                    for nid in candidates
                ]
                if weights and sum(weights) > 0:
                    weights = np.array(weights) / sum(weights)
                    n_targets = min(3, len(candidates))
                    return np.random.choice(candidates, size=n_targets, p=weights, replace=False).tolist()
                return candidates[:3]

    async def _propagate_to_node(
        self,
        alert: FederatedAlert,
        target_node_id: str
    ) -> bool:
        """Propaga alerta para nó específico."""
        start_time = time.time()

        # Verificar TTL
        if alert.ttl_hops <= 0:
            logging.debug(f"⏭️ Alert {alert.alert_id} TTL expired for {target_node_id}")
            return False

        # Decrementar TTL para próxima propagação
        alert_with_reduced_ttl = FederatedAlert(
            **alert.to_dict(),
            ttl_hops=alert.ttl_hops - 1
        )

        # Preparar mensagem de propagação
        propagation_msg = {
            'type': 'ALERT_PROPAGATION',
            'alert': alert_with_reduced_ttl.to_dict(),
            'propagated_by': self.node_id,
            'hop_count': 5 - alert.ttl_hops + 1,  # Contar hops
            'timestamp': time.time()
        }

        # Assinar mensagem de propagação
        if self.key_manager:
            propagation_msg['signature'] = self.key_manager.sign_content(
                json.dumps(propagation_msg, sort_keys=True)
            )

        # Enviar para nó alvo (simulado)
        # Em produção: enviar via protocolo P2P com retry
        logging.debug(f"📤 Propagating alert {alert.alert_id[:8]} to {target_node_id} (hop {propagation_msg['hop_count']})")

        # Simular latência de rede baseada em "distância cósmica"
        # (simplificação: latência aleatória entre 10-100ms)
        network_latency = np.random.uniform(0.01, 0.1)
        await asyncio.sleep(network_latency)

        # Em produção: chamar camada de rede real
        # success = await network_layer.send(target_node_id, propagation_msg)
        success = True  # Simular sucesso

        # Atualizar métricas de latência
        latency_ms = (time.time() - start_time) * 1000
        old_avg = self.propagation_stats['avg_propagation_latency_ms']
        n = self.propagation_stats['alerts_propagated'] + 1
        self.propagation_stats['avg_propagation_latency_ms'] = (
            (old_avg * (n - 1) + latency_ms) / n if n > 1 else latency_ms
        )

        return success

    async def handle_received_alert(
        self,
        alert_data: Dict,
        propagated_by: str,
        hop_count: int
    ) -> bool:
        """
        Manipula alerta recebido de outro observatório.
        Retorna True se alerta foi processado, False se ignorado (duplicado/inválido).
        """
        alert_id = alert_data.get('alert_id')

        # Verificar duplicação
        if alert_id in self.processed_alerts:
            self.propagation_stats['alerts_deduplicated'] += 1
            logging.debug(f"⏭️ Duplicate alert ignored: {alert_id}")
            return False

        # Verificar assinatura
        if not self._verify_alert_signature(alert_data):
            logging.warning(f"❌ Invalid signature on alert {alert_id}")
            return False

        # Reconstruir objeto FederatedAlert
        alert = FederatedAlert(**alert_data)

        # Verificar TTL
        if alert.ttl_hops <= 0:
            logging.debug(f"⏭️ Alert {alert_id} TTL expired")
            return False

        # Registrar como processado
        self.processed_alerts.add(alert_id)
        self.propagation_stats['alerts_received'] += 1
        self.alert_history.append(alert.to_dict())

        # Processar alerta localmente
        await self._process_alert_locally(alert)

        # Re-propagar se TTL permitir e modo permitir
        if alert.ttl_hops > 0 and alert.propagation_mode != AlertPropagationMode.TARGETED:
            # Enfileirar para propagação adicional
            await self.propagation_queue.put(alert)

        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                callback({
                    'type': 'alert_received',
                    'alert': alert.to_dict(),
                    'propagated_by': propagated_by,
                    'hop_count': hop_count,
                    'processed_at': time.time()
                })
            except Exception as e:
                logging.error(f"⚠️ Alert callback error: {e}")

        return True

    def _verify_alert_signature(self, alert_data: Dict) -> bool:
        """Verifica assinatura criptográfica de alerta recebido."""
        if not self.key_manager:
            return True  # Modo desenvolvimento

        # Extrair campos para verificação (excluindo signature)
        alert_copy = {k: v for k, v in alert_data.items() if k != 'signature'}
        signature = alert_data.get('signature', '')

        # Verificar assinatura
        return self.key_manager.verify_signature(
            content_hash=json.dumps(alert_copy, sort_keys=True),
            signature=signature,
            signer_node_id=alert_data.get('source_node_id')
        )

    async def _process_alert_locally(self, alert: FederatedAlert):
        """Processa alerta localmente (dispara ações, notificações, etc.)."""
        logging.info(f"🔔 Alert processed locally: {alert.alert_type} ({alert.severity.value})")

        # Ações baseadas na severidade
        if alert.severity == AlertSeverity.COSMIC_EMERGENCY:
            # Emergência cósmica: disparar protocolos de contenção imediata
            await self._trigger_cosmic_emergency_response(alert)
        elif alert.severity == AlertSeverity.CRITICAL:
            # Crítico: notificar equipe humana imediatamente
            await self._escalate_to_human_operators(alert)

        # Registrar no audit log federado (se disponível)
        # Em produção: registrar em DistributedAuditLedger

    async def _trigger_cosmic_emergency_response(self, alert: FederatedAlert):
        """Dispara resposta de emergência para alertas cósmicos críticos."""
        logging.critical(f"🚨 COSMIC EMERGENCY: {alert.description}")

        # Ações automáticas de contenção (exemplos)
        emergency_actions = [
            "Isolar zonas afetadas da Hyper-Mesh",
            "Ativar protocolos de re-emaranhamento de emergência",
            "Reduzir carga computacional em nós críticos",
            "Notificar todos os observatórios via canal prioritário"
        ]

        for action in emergency_actions:
            logging.info(f"🛡️  Executando ação de emergência: {action}")
            # Em produção: chamar sistemas de resposta automática
            await asyncio.sleep(0.05)  # Simular execução

    async def _escalate_to_human_operators(self, alert: FederatedAlert):
        """Escalona alerta crítico para operadores humanos."""
        # Em produção: integrar com sistema de notificação (Slack, PagerDuty, etc.)
        escalation_message = (
            f"🚨 ALERTA CRÍTICO FEDERADO\n"
            f"Tipo: {alert.alert_type}\n"
            f"Severidade: {alert.severity.value}\n"
            f"Origem: {alert.source_node_id}\n"
            f"Descrição: {alert.description}\n"
            f"Métricas afetadas: {', '.join(alert.affected_metrics)}"
        )

        logging.critical(f"📢 Escalando para operadores humanos:\n{escalation_message}")

        # Simular envio de notificação
        await asyncio.sleep(0.1)

    def register_alert_callback(self, callback: Callable[[Dict], None]):
        """Registra callback para notificação de alertas recebidos."""
        self.alert_callbacks.append(callback)

    def get_alert_history(
        self,
        severity_filter: Optional[AlertSeverity] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Retorna histórico de alertas, opcionalmente filtrado."""
        alerts = list(self.alert_history)

        if severity_filter:
            alerts = [a for a in alerts if a['severity'] == severity_filter.value]

        return sorted(alerts, key=lambda a: a['timestamp'], reverse=True)[:limit]

    def get_propagation_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de propagação de alertas."""
        return {
            **self.propagation_stats,
            'processed_alerts_count': len(self.processed_alerts),
            'queue_size': self.propagation_queue.qsize(),
            'propagation_task_running': self._propagation_task and not self._propagation_task.done()
        }

    async def shutdown(self):
        """Encerra gracefully o sistema de propagação."""
        if self._propagation_task and not self._propagation_task.done():
            self._propagation_task.cancel()
            try:
                await self._propagation_task
            except asyncio.CancelledError:
                pass
        logging.info("🛑 FederatedAlertPropagation shutdown complete")
