#!/usr/bin/env python3
"""
cosmic_federation_orchestrator.py — Orquestrador principal da federação
de métricas cósmicas entre múltiplos observatórios ARKHE.
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import logging

class FederationState(Enum):
    """Estados da federação de observatórios."""
    INITIALIZING = auto()
    DISCOVERING = auto()
    SYNCHRONIZING = auto()
    OPERATIONAL = auto()
    DEGRADED = auto()
    OFFLINE = auto()

@dataclass
class FederationConfig:
    """Configuração da federação de observatórios cósmicos."""
    federation_id: str
    node_id: str
    initial_peers: List[str]
    consensus_config: Dict[str, Any]
    aggregation_config: Dict[str, Any]
    discovery_config: Dict[str, Any]
    alert_config: Dict[str, Any]
    audit_config: Dict[str, Any]
    key_manager_path: Optional[str] = None
    data_directory: str = './federation_data'

class CosmicFederationOrchestrator:
    """
    Orquestrador central da federação de métricas cósmicas.
    Coordena consenso, agregação, descoberta, alertas e auditoria
    entre múltiplos observatórios ARKHE.
    """

    def __init__(self, config: FederationConfig):
        self.config = config
        self.state = FederationState.INITIALIZING

        # Componentes da federação (inicializados em _initialize_components)
        self.key_manager = None
        self.consensus_protocol = None
        self.metric_aggregator = None
        self.observatory_discovery = None
        self.alert_propagation = None
        self.audit_ledger = None

        # Estado da federação
        self.federation_members: Dict[str, Dict] = {}
        self.shared_metrics: Dict[str, Any] = {}
        self.active_alerts: Dict[str, Dict] = {}

        # Callbacks para integração externa
        self.federation_callbacks: List[Callable] = []

        # Métricas da federação
        self.federation_metrics = {
            'uptime_sec': 0.0,
            'consensus_rounds': 0,
            'federated_aggregations': 0,
            'alerts_propagated': 0,
            'audit_entries': 0,
            'active_members': 0
        }

        logging.info(f"🌌 CosmicFederationOrchestrator initialized: {config.federation_id}")

    def _initialize_components(self):
        """Inicializa todos os componentes da federação."""
        # Carregar ou criar KeyManager
        if self.config.key_manager_path:
            from arkhe_os.crypto._key_rotation import KeyManager
            self.key_manager = KeyManager.load(self.config.key_manager_path)
        else:
            # Criar KeyManager temporário para desenvolvimento
            from arkhe_os.crypto._key_rotation import KeyManager
            self.key_manager = KeyManager(node_id=self.config.node_id)

        # Inicializar protocolo de consenso
        from .cosmic_consensus_protocol import CosmicConsensusProtocol
        self.consensus_protocol = CosmicConsensusProtocol(
            node_id=self.config.node_id,
            federation_config=self.config.consensus_config,
            key_manager=self.key_manager
        )

        # Inicializar agregador federado
        from .federated_metric_aggregator import FederatedMetricAggregator
        self.metric_aggregator = FederatedMetricAggregator(
            node_id=self.config.node_id,
            default_strategy=self.config.aggregation_config.get('default_strategy'),
            dp_enabled=self.config.aggregation_config.get('privacy_enabled', True),
            consensus_protocol=self.consensus_protocol
        )

        # Inicializar descoberta de observatórios
        from .observatory_discovery import ObservatoryDiscoveryProtocol
        self.observatory_discovery = ObservatoryDiscoveryProtocol(
            node_id=self.config.node_id,
            federation_config=self.config.discovery_config,
            key_manager=self.key_manager,
            known_observatories={
                peer: {'federation_role': 'validator', 'trust_score': 0.9}
                for peer in self.config.initial_peers
            }
        )

        # Inicializar propagação de alertas
        from .federated_alert_propagation import FederatedAlertPropagation, AlertPropagationMode
        self.alert_propagation = FederatedAlertPropagation(
            node_id=self.config.node_id,
            federation_config=self.config.alert_config,
            known_observatories={
                peer: {'federation_role': 'validator'}
                for peer in self.config.initial_peers
            },
            key_manager=self.key_manager
        )

        # Inicializar ledger de auditoria distribuído
        from .distributed_audit_ledger import DistributedAuditLedger
        self.audit_ledger = DistributedAuditLedger(
            node_id=self.config.node_id,
            federation_config=self.config.audit_config,
            key_manager=self.key_manager,
            ledger_path=Path(self.config.data_directory) / 'audit_ledger'
        )

        # Registrar callbacks entre componentes
        self._wire_component_callbacks()

        logging.info(f"✅ All federation components initialized")

    def _wire_component_callbacks(self):
        """Conecta callbacks entre componentes para integração."""
        # Consensus → Ledger: registrar métricas decididas
        def on_consensus_decided(event: Dict):
            asyncio.create_task(self.audit_ledger.append_entry(
                entry_type='METRIC_CONSENSUS',
                data=event['proposal'],
                metadata={'consensus_epoch': event.get('epoch')}
            ))

        self.consensus_protocol.register_consensus_callback(on_consensus_decided)

        # Aggregator → Ledger: registrar agregações federadas
        def on_aggregation_completed(result: Dict):
            asyncio.create_task(self.audit_ledger.append_entry(
                entry_type='METRIC_CONSENSUS',
                data=result,
                metadata={'aggregation_strategy': result.get('aggregation_strategy')}
            ))
            self.federation_metrics['federated_aggregations'] += 1

        self.metric_aggregator.register_aggregation_callback(on_aggregation_completed)

        # Discovery → Ledger: registrar admissões de observatórios
        def on_observatory_admitted(event: Dict):
            asyncio.create_task(self.audit_ledger.append_entry(
                entry_type='NODE_ADMISSION',
                data=event['identity'],
                metadata={'admitted_by': event.get('admitted_by')}
            ))
            # Atualizar lista de membros
            self.federation_members[event['identity']['node_id']] = event['identity']
            self.federation_metrics['active_members'] = len(self.federation_members)

        self.observatory_discovery.register_discovery_callback(on_observatory_admitted)

        # Alert Propagation → Ledger: registrar alertas propagados
        def on_alert_received(event: Dict):
            asyncio.create_task(self.audit_ledger.append_entry(
                entry_type='ALERT_PROPAGATION',
                data=event['alert'],
                metadata={
                    'propagated_by': event.get('propagated_by'),
                    'hop_count': event.get('hop_count')
                }
            ))
            self.federation_metrics['alerts_propagated'] += 1

            # Atualizar alertas ativos
            alert_id = event['alert']['alert_id']
            self.active_alerts[alert_id] = {
                **event['alert'],
                'received_at': event.get('processed_at'),
                'propagation_hops': event.get('hop_count')
            }

        self.alert_propagation.register_alert_callback(on_alert_received)

        # Ledger → Metrics: atualizar contagem de entradas de auditoria
        def on_ledger_entry_appended(event: Dict):
            self.federation_metrics['audit_entries'] += 1

        self.audit_ledger.register_ledger_callback(on_ledger_entry_appended)

    async def start(self):
        """Inicia a federação de observatórios."""
        logging.info(f"🚀 Starting Cosmic Federation: {self.config.federation_id}")

        # Inicializar componentes
        self._initialize_components()

        # Mudar estado para descoberta
        self.state = FederationState.DISCOVERING

        # Iniciar descoberta de observatórios
        await self._begin_observatory_discovery()

        # Aguardar sincronização inicial
        await self._wait_for_initial_sync()

        # Mudar para estado operacional
        self.state = FederationState.OPERATIONAL
        self.federation_metrics['start_time'] = time.time()

        # Registrar entrada de inicialização no ledger
        await self.audit_ledger.append_entry(
            entry_type=LedgerEntryType.SYSTEM_HEALTH,
            data={
                'federation_id': self.config.federation_id,
                'node_id': self.config.node_id,
                'initial_peers': self.config.initial_peers,
                'components_initialized': [
                    'consensus', 'aggregation', 'discovery', 'alerts', 'audit'
                ]
            },
            metadata={'federation_state': 'OPERATIONAL'}
        )

        logging.info(f"✅ Federation {self.config.federation_id} is now OPERATIONAL")

        # Iniciar loop de métricas de saúde
        asyncio.create_task(self._health_monitoring_loop())

    async def _begin_observatory_discovery(self):
        """Inicia protocolo de descoberta de observatórios."""
        logging.info(f"🔍 Beginning observatory discovery with {len(self.config.initial_peers)} initial peers")

        # Anunciar este nó para a federação
        await self.observatory_discovery.announce_observatory(
            public_key=self.key_manager.get_public_key() if self.key_manager else 'dev_key',
            federation_role='validator',
            capabilities={
                'supported_metrics': [
                    'cosmic.phi_c_global',
                    'cosmic.entanglement_health',
                    'operations.response_time_p99',
                    'security.anomaly_rate'
                ],
                'aggregation_strategies': ['weighted_average', 'median', 'dp_aggregate'],
                'consensus_participant': True,
                'alert_propagation_enabled': True
            },
            request_pow=True
        )

    async def _wait_for_initial_sync(self, timeout_sec: float = 30.0):
        """Aguarda sincronização inicial com a federação."""
        start_time = time.time()
        self.state = FederationState.SYNCHRONIZING

        logging.info(f"⏳ Waiting for initial federation sync (timeout={timeout_sec}s)")

        while time.time() - start_time < timeout_sec:
            # Verificar se temos pelo menos um peer sincronizado
            active_peers = len([
                m for m in self.federation_members.values()
                if m.get('last_heartbeat', 0) > time.time() - 60
            ])

            if active_peers >= 1:  # Pelo menos 1 peer ativo
                logging.info(f"✅ Initial sync achieved with {active_peers} active peer(s)")
                return

            await asyncio.sleep(1.0)

        logging.warning(f"⚠️ Initial sync timeout — proceeding with {len(self.federation_members)} known members")

    async def submit_local_metric(
        self,
        metric_name: str,
        metric_value: float,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Submete métrica local para agregação federada.

        Returns:
            True se submetido com sucesso
        """
        if self.state != FederationState.OPERATIONAL:
            logging.warning(f"⚠️ Cannot submit metric: federation not operational (state={self.state.name})")
            return False

        # Submeter para agregador federado
        observation = self.metric_aggregator.submit_local_observation(
            metric_name=metric_name,
            local_value=metric_value,
            confidence=confidence,
            metadata=metadata
        )

        # Tentar agregar imediatamente se for métrica crítica
        if metadata and metadata.get('critical', False):
            await self.metric_aggregator.aggregate_federated_metric(
                metric_name=metric_name,
                require_consensus=True
            )

        return True

    async def get_federated_metric(
        self,
        metric_name: str,
        strategy: Optional[str] = None,
        require_consensus: bool = True
    ) -> Optional[Dict]:
        """
        Obtém valor federado de métrica após agregação e consenso.

        Returns:
            Dict com resultado federado ou None se indisponível
        """
        if self.state != FederationState.OPERATIONAL:
            return None

        from .federated_metric_aggregator import AggregationStrategy
        strategy_enum = None
        if strategy:
            try:
                strategy_enum = AggregationStrategy[strategy.upper()]
            except KeyError:
                logging.warning(f"⚠️ Unknown aggregation strategy: {strategy}")

        result = await self.metric_aggregator.aggregate_federated_metric(
            metric_name=metric_name,
            strategy=strategy_enum,
            require_consensus=require_consensus
        )

        if result:
            # Cache do resultado compartilhado
            self.shared_metrics[metric_name] = result.to_dict()
            return result.to_dict()

        # Fallback para último valor conhecido
        return self.shared_metrics.get(metric_name)

    async def propagate_critical_alert(
        self,
        alert_type: str,
        severity: str,
        description: str,
        affected_metrics: List[str],
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Propaga alerta crítico através da federação.

        Returns:
            True se alerta foi propagado
        """
        from .federated_alert_propagation import AlertSeverity, AlertPropagationMode

        # Mapear string para enum
        try:
            severity_enum = AlertSeverity[severity.upper()]
        except KeyError:
            logging.error(f"❌ Invalid alert severity: {severity}")
            return False

        # Determinar modo de propagação baseado na severidade
        if severity_enum == AlertSeverity.COSMIC_EMERGENCY:
            mode = AlertPropagationMode.FLOOD
        elif severity_enum == AlertSeverity.CRITICAL:
            mode = AlertPropagationMode.HIERARCHICAL
        else:
            mode = AlertPropagationMode.ADAPTIVE

        # Criar e propagar alerta
        alert = await self.alert_propagation.create_and_propagate_alert(
            alert_type=alert_type,
            severity=severity_enum,
            description=description,
            affected_metrics=affected_metrics,
            metadata=metadata,
            propagation_mode=mode
        )

        return alert is not None

    def get_federation_health(self) -> Dict[str, Any]:
        """Retorna saúde consolidada da federação."""
        consensus_health = self.consensus_protocol.get_consensus_status() if self.consensus_protocol else {}
        aggregator_health = self.metric_aggregator.get_aggregator_health() if self.metric_aggregator else {}
        discovery_health = self.observatory_discovery.get_discovery_status() if self.observatory_discovery else {}
        alert_health = self.alert_propagation.get_propagation_stats() if self.alert_propagation else {}
        audit_health = self.audit_ledger.get_ledger_health() if self.audit_ledger else {}

        # Calcular saúde geral da federação
        components_healthy = sum([
            consensus_health.get('metrics', {}).get('consensus_rounds_completed', 0) > 0,
            aggregator_health.get('federated_results_count', 0) > 0,
            discovery_health.get('known_observatories_count', 0) >= 1,
            audit_health.get('total_entries', 0) > 0
        ])

        overall_health = 'healthy' if components_healthy >= 3 else 'degraded' if components_healthy >= 1 else 'critical'

        return {
            'federation_id': self.config.federation_id,
            'node_id': self.config.node_id,
            'state': self.state.name,
            'overall_health': overall_health,
            'uptime_sec': time.time() - self.federation_metrics.get('start_time', time.time()),
            'active_members': self.federation_metrics['active_members'],
            'metrics': self.federation_metrics,
            'components': {
                'consensus': consensus_health,
                'aggregation': aggregator_health,
                'discovery': discovery_health,
                'alerts': alert_health,
                'audit': audit_health
            },
            'shared_metrics_summary': {
                name: {
                    'value': result.get('aggregated_value'),
                    'confidence': result.get('confidence_interval'),
                    'last_updated': result.get('timestamp')
                }
                for name, result in self.shared_metrics.items()
            },
            'active_alerts_count': len([
                a for a in self.active_alerts.values()
                if time.time() - a.get('received_at', 0) < 3600  # Últimos 60 minutos
            ])
        }

    def register_federation_callback(self, callback: Callable[[Dict], None]):
        """Registra callback para eventos da federação."""
        self.federation_callbacks.append(callback)

    async def shutdown(self):
        """Encerra gracefully a federação."""
        logging.info(f"🛑 Shutting down federation {self.config.federation_id}")

        self.state = FederationState.OFFLINE

        # Encerrar componentes
        if self.alert_propagation:
            await self.alert_propagation.shutdown()

        # Registrar entrada de shutdown no ledger
        if self.audit_ledger:
            await self.audit_ledger.append_entry(
                entry_type=LedgerEntryType.SYSTEM_HEALTH,
                data={
                    'shutdown_reason': 'graceful_shutdown',
                    'final_metrics': self.federation_metrics,
                    'active_members_at_shutdown': len(self.federation_members)
                }
            )

        logging.info(f"✅ Federation shutdown complete")

    async def _health_monitoring_loop(self, interval_sec: float = 60.0):
        """Loop de monitoramento de saúde da federação."""
        while self.state == FederationState.OPERATIONAL:
            try:
                # Coletar métricas de saúde dos componentes
                health_report = self.get_federation_health()

                # Verificar condições de degradação
                if health_report['overall_health'] == 'degraded':
                    logging.warning(f"⚠️ Federation health degraded: {health_report}")
                    self.state = FederationState.DEGRADED

                    # Disparar alerta federado se degradação persistente
                    if health_report['uptime_sec'] > 300:  # Após 5 minutos
                        await self.propagate_critical_alert(
                            alert_type='federation_health_degradation',
                            severity='warning',
                            description=f"Federation health degraded: {health_report['overall_health']}",
                            affected_metrics=['federation.overall_health'],
                            metadata={'health_report': health_report}
                        )

                # Registrar snapshot de saúde no ledger periodicamente
                if int(time.time()) % 300 == 0:  # A cada 5 minutos
                    await self.audit_ledger.append_entry(
                        entry_type=LedgerEntryType.SYSTEM_HEALTH,
                        data=health_report,
                        metadata={'snapshot': True}
                    )

                # Notificar callbacks
                for callback in self.federation_callbacks:
                    try:
                        callback({'type': 'health_update', 'health': health_report})
                    except Exception as e:
                        logging.error(f"⚠️ Federation callback error: {e}")

                await asyncio.sleep(interval_sec)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"⚠️ Health monitoring loop error: {e}")
                await asyncio.sleep(interval_sec)
