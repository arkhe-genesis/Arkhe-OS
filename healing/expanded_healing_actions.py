#!/usr/bin/env python3
"""
Substrato 199.3: Expanded Healing Actions
Expande o Auto-Healing Orchestrator para 15+ ações mapeadas
para cobertura completa de anomalias em produção.
"""

from enum import Enum, auto
from typing import Dict, List, Callable, Optional, Any
import time
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExpandedHealingAction(Enum):
    """Ações expandidas de auto-healing (15+)."""
    # Ações originais (8)
    RESTART_SERVICE = "restart_service"
    ISOLATE_PROCESS = "isolate_process"
    ROLLBACK_DRIVER = "rollback_driver"
    FLUSH_MEMORY = "flush_memory"
    RESET_NETWORK = "reset_network"
    RESTORE_REGISTRY = "restore_registry"
    TRIGGER_FAILOVER = "trigger_failover"
    NOTIFY_OPERATOR = "notify_operator"

    # Novas ações expandidas (7+)
    SCALE_UP_RESOURCES = "scale_up_resources"           # Aumentar CPU/memória
    SCALE_DOWN_RESOURCES = "scale_down_resources"       # Liberar recursos ociosos
    ROTATE_CREDENTIALS = "rotate_credentials"           # Rotação preventiva de credenciais
    UPDATE_FIREWALL_RULES = "update_firewall_rules"     # Atualizar regras de firewall
    CLEAR_CACHE_LAYERS = "clear_cache_layers"           # Limpar caches em cascata
    REBALANCE_LOAD = "rebalance_load"                   # Rebalancear carga entre nós
    ACTIVATE_CIRCUIT_BREAKER = "activate_circuit_breaker"  # Ativar circuit breaker
    TRIGGER_HEALTH_CHECK = "trigger_health_check"       # Forçar health check profundo
    REVOKE_SESSIONS = "revoke_sessions"                 # Revogar sessões suspeitas
    UPDATE_DNS_CACHE = "update_dns_cache"               # Atualizar cache DNS
    FLUSH_CONNECTION_POOL = "flush_connection_pool"     # Limpar pool de conexões
    RESTART_DEPENDENT_SERVICES = "restart_dependent_services"  # Reiniciar serviços dependentes
    APPLY_SECURITY_PATCH = "apply_security_patch"       # Aplicar patch de segurança crítico
    ENABLE_RATE_LIMITING = "enable_rate_limiting"       # Ativar rate limiting emergencial
    TRIGGER_BACKUP_RECOVERY = "trigger_backup_recovery" # Acionar recuperação de backup

class ExpandedHealingOrchestrator:
    """
    Orquestrador expandido com 15+ ações de auto-healing.

    Mapeamento feature → ações (expandido):
    • handle_count elevado → ISOLATE_PROCESS, RESTART_SERVICE, FLUSH_CONNECTION_POOL
    • signature_valid=False → RESTORE_REGISTRY, ROLLBACK_DRIVER, APPLY_SECURITY_PATCH
    • phi_c_contribution baixo → FLUSH_MEMORY, RESET_NETWORK, REBALANCE_LOAD
    • cpu_percent alto → SCALE_UP_RESOURCES, RESTART_SERVICE, TRIGGER_FAILOVER
    • memory_mb alto → FLUSH_MEMORY, CLEAR_CACHE_LAYERS, SCALE_UP_RESOURCES
    • network_bytes anômalo → UPDATE_FIREWALL_RULES, ENABLE_RATE_LIMITING, RESET_NETWORK
    • disk_io_mbps alto → CLEAR_CACHE_LAYERS, SCALE_UP_RESOURCES, TRIGGER_BACKUP_RECOVERY
    • thread_count elevado → RESTART_SERVICE, ISOLATE_PROCESS, RESTART_DEPENDENT_SERVICES
    • latency_ms alto → REBALANCE_LOAD, RESET_NETWORK, ACTIVATE_CIRCUIT_BREAKER
    • error_rate elevado → TRIGGER_HEALTH_CHECK, NOTIFY_OPERATOR, APPLY_SECURITY_PATCH
    """

    # Mapeamento expandido feature → ações candidatas
    FEATURE_HEALING_MAP = {
        "handle_count": [
            ExpandedHealingAction.ISOLATE_PROCESS,
            ExpandedHealingAction.RESTART_SERVICE,
            ExpandedHealingAction.FLUSH_CONNECTION_POOL
        ],
        "thread_count": [
            ExpandedHealingAction.ISOLATE_PROCESS,
            ExpandedHealingAction.RESTART_SERVICE,
            ExpandedHealingAction.RESTART_DEPENDENT_SERVICES
        ],
        "signature_valid": [
            ExpandedHealingAction.RESTORE_REGISTRY,
            ExpandedHealingAction.ROLLBACK_DRIVER,
            ExpandedHealingAction.APPLY_SECURITY_PATCH
        ],
        "hsm_signed": [
            ExpandedHealingAction.RESTORE_REGISTRY,
            ExpandedHealingAction.ROTATE_CREDENTIALS,
            ExpandedHealingAction.NOTIFY_OPERATOR
        ],
        "phi_c_contribution": [
            ExpandedHealingAction.FLUSH_MEMORY,
            ExpandedHealingAction.RESET_NETWORK,
            ExpandedHealingAction.REBALANCE_LOAD
        ],
        "cpu_percent": [
            ExpandedHealingAction.SCALE_UP_RESOURCES,
            ExpandedHealingAction.RESTART_SERVICE,
            ExpandedHealingAction.TRIGGER_FAILOVER
        ],
        "memory_mb": [
            ExpandedHealingAction.FLUSH_MEMORY,
            ExpandedHealingAction.CLEAR_CACHE_LAYERS,
            ExpandedHealingAction.SCALE_UP_RESOURCES
        ],
        "disk_io_mbps": [
            ExpandedHealingAction.RESTART_SERVICE,
            ExpandedHealingAction.SCALE_UP_RESOURCES,
            ExpandedHealingAction.TRIGGER_BACKUP_RECOVERY
        ],
        "network_bytes": [
            ExpandedHealingAction.UPDATE_FIREWALL_RULES,
            ExpandedHealingAction.ENABLE_RATE_LIMITING,
            ExpandedHealingAction.RESET_NETWORK
        ],
        "latency_ms": [
            ExpandedHealingAction.REBALANCE_LOAD,
            ExpandedHealingAction.RESET_NETWORK,
            ExpandedHealingAction.ACTIVATE_CIRCUIT_BREAKER
        ],
        "error_rate": [
            ExpandedHealingAction.TRIGGER_HEALTH_CHECK,
            ExpandedHealingAction.NOTIFY_OPERATOR,
            ExpandedHealingAction.APPLY_SECURITY_PATCH
        ],
    }

    # Thresholds de autonomia expandidos
    AUTONOMY_THRESHOLDS = {
        "full_auto": {"min_phi_c": 0.99, "max_risk": "medium"},
        "auto_with_notify": {"min_phi_c": 0.95, "max_risk": "high"},
        "human_required": {"min_phi_c": 0.0, "max_risk": "any"}
    }

    def __init__(
        self,
        phi_bus=None,
        temporal_chain=None,
        guardian=None,
        k8s_client=None,
        config_db=None
    ):
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.guardian = guardian
        self.k8s = k8s_client
        self.config_db = config_db
        self._action_handlers: Dict[ExpandedHealingAction, Callable] = {}
        self._healing_history: List[Dict] = []
        self._circuit_breakers_state = {}  # service_name -> {"state": "closed"|"open"|"half-open", "failures": 0}
        self._register_expanded_handlers()

    async def _request_multi_agent_consensus(self, action: ExpandedHealingAction, anomaly_alert: Dict) -> bool:
        """
        Solicita consenso multi-agente (via barramento) antes de executar ações destrutivas.
        Ações destrutivas precisam de aprovação de instâncias adicionais do Sentinel.
        """
        destructive_actions = {
            ExpandedHealingAction.RESTART_SERVICE,
            ExpandedHealingAction.ISOLATE_PROCESS,
            ExpandedHealingAction.TRIGGER_FAILOVER,
            ExpandedHealingAction.APPLY_SECURITY_PATCH,
            ExpandedHealingAction.REVOKE_SESSIONS
        }

        if action not in destructive_actions:
            return True  # Ações seguras passam direto

        logger.info(f"🤝 Solicitando consenso multi-agente para ação destrutiva: {action.value}")

        # Simula barramento: publica pedido de consenso e aguarda respostas
        if self.phi_bus:
            await self.phi_bus.publish_metric("healing_consensus_request", {
                "action": action.value,
                "alert_id": anomaly_alert.get("alert_id", "unknown")
            })

        await asyncio.sleep(0.5)  # Simula tempo de rede
        # Mock: Assume que a malha aprovou a ação
        logger.info(f"✅ Consenso multi-agente alcançado para {action.value}")
        return True

    def _register_expanded_handlers(self):
        """Registra handlers para todas as 15+ ações."""
        self._action_handlers = {
            # Handlers originais
            ExpandedHealingAction.RESTART_SERVICE: self._restart_service,
            ExpandedHealingAction.ISOLATE_PROCESS: self._isolate_process,
            ExpandedHealingAction.FLUSH_MEMORY: self._flush_memory,
            ExpandedHealingAction.RESET_NETWORK: self._reset_network,
            ExpandedHealingAction.RESTORE_REGISTRY: self._restore_registry,
            ExpandedHealingAction.NOTIFY_OPERATOR: self._notify_operator,
            ExpandedHealingAction.TRIGGER_FAILOVER: self._trigger_failover,
            ExpandedHealingAction.ROLLBACK_DRIVER: self._rollback_driver,

            # Handlers expandidos
            ExpandedHealingAction.SCALE_UP_RESOURCES: self._scale_up_resources,
            ExpandedHealingAction.SCALE_DOWN_RESOURCES: self._scale_down_resources,
            ExpandedHealingAction.ROTATE_CREDENTIALS: self._rotate_credentials,
            ExpandedHealingAction.UPDATE_FIREWALL_RULES: self._update_firewall_rules,
            ExpandedHealingAction.CLEAR_CACHE_LAYERS: self._clear_cache_layers,
            ExpandedHealingAction.REBALANCE_LOAD: self._rebalance_load,
            ExpandedHealingAction.ACTIVATE_CIRCUIT_BREAKER: self._activate_circuit_breaker,
            ExpandedHealingAction.TRIGGER_HEALTH_CHECK: self._trigger_health_check,
            ExpandedHealingAction.REVOKE_SESSIONS: self._revoke_sessions,
            ExpandedHealingAction.UPDATE_DNS_CACHE: self._update_dns_cache,
            ExpandedHealingAction.FLUSH_CONNECTION_POOL: self._flush_connection_pool,
            ExpandedHealingAction.RESTART_DEPENDENT_SERVICES: self._restart_dependent_services,
            ExpandedHealingAction.APPLY_SECURITY_PATCH: self._apply_security_patch,
            ExpandedHealingAction.ENABLE_RATE_LIMITING: self._enable_rate_limiting,
            ExpandedHealingAction.TRIGGER_BACKUP_RECOVERY: self._trigger_backup_recovery,
        }

    async def _scale_up_resources(self, anomaly_alert: Dict) -> bool:
        """Aumenta recursos (CPU/memória) via Kubernetes."""
        if not self.k8s:
            logger.warning("⚠️  K8s client não disponível — scale-up simulado")
            return True

        target = anomaly_alert.get("executable_path", "unknown").split("\\")[-1]
        logger.info(f"⬆️  Scale-up de recursos para: {target}")

        # Mock: em produção, chamar K8s API para aumentar limits/requests
        await asyncio.sleep(0.3)
        return True

    async def _scale_down_resources(self, anomaly_alert: Dict) -> bool:
        """Diminui recursos."""
        return True

    async def _rotate_credentials(self, anomaly_alert: Dict) -> bool:
        """Rotação preventiva de credenciais."""
        service = anomaly_alert.get("executable_path", "unknown")
        logger.info(f"🔄 Rotação de credenciais para: {service}")

        # Mock: em produção, chamar Vault/Secrets Manager
        await asyncio.sleep(0.2)
        return True

    async def _update_firewall_rules(self, anomaly_alert: Dict) -> bool:
        """Atualiza regras de firewall baseado em anomalia de rede."""
        logger.info(f"🔥 Atualizando regras de firewall...")

        # Mock: em produção, chamar API do firewall/NSG
        await asyncio.sleep(0.4)
        return True

    async def _clear_cache_layers(self, anomaly_alert: Dict) -> bool:
        """Limpa caches em cascata (app, DB, CDN)."""
        logger.info(f"🧹 Limpando camadas de cache...")

        # Mock: em produção, chamar endpoints de cache de cada camada
        await asyncio.sleep(0.25)
        return True

    async def _rebalance_load(self, anomaly_alert: Dict) -> bool:
        """Rebalanceia carga entre nós do cluster."""
        logger.info(f"⚖️  Rebalanceando carga do cluster...")

        # Mock: em produção, chamar load balancer API
        await asyncio.sleep(0.35)
        return True

    async def _activate_circuit_breaker(self, anomaly_alert: Dict) -> bool:
        """Ativa circuit breaker distribuído (cross-service) para o serviço afetado."""
        service = anomaly_alert.get("executable_path", "unknown")
        logger.info(f"🔌 Ativando circuit breaker (Estado: OPEN) para: {service}")

        # Atualiza estado interno
        self._circuit_breakers_state[service] = {"state": "open", "opened_at": time.time()}

        # Notifica serviços dependentes via barramento
        if self.phi_bus:
            await self.phi_bus.publish_metric("circuit_breaker_state_changed", {
                "service": service,
                "new_state": "open",
                "reason": "Anomaly threshold reached"
            })

        # Mock: em produção, atualizar config do circuit breaker
        await asyncio.sleep(0.15)
        return True

    async def _trigger_health_check(self, anomaly_alert: Dict) -> bool:
        """Força health check profundo do serviço."""
        service = anomaly_alert.get("executable_path", "unknown")
        logger.info(f"🏥 Triggering deep health check: {service}")

        # Mock: em produção, chamar endpoint /health?deep=true
        await asyncio.sleep(0.2)
        return True

    async def _revoke_sessions(self, anomaly_alert: Dict) -> bool:
        """Revoga sessões suspeitas de usuários."""
        logger.info(f"🔐 Revogando sessões suspeitas...")

        # Mock: em produção, chamar auth service para invalidar tokens
        await asyncio.sleep(0.18)
        return True

    async def _update_dns_cache(self, anomaly_alert: Dict) -> bool:
        """Atualiza cache DNS para resolver problemas de resolução."""
        logger.info(f"🌐 Atualizando cache DNS...")

        # Mock: em produção, chamar comando de flush DNS
        await asyncio.sleep(0.12)
        return True

    async def _flush_connection_pool(self, anomaly_alert: Dict) -> bool:
        """Limpa pool de conexões para resolver vazamentos."""
        service = anomaly_alert.get("executable_path", "unknown")
        logger.info(f"💧 Flushing connection pool: {service}")

        # Mock: em produção, chamar endpoint de admin do service
        await asyncio.sleep(0.22)
        return True

    async def _restart_dependent_services(self, anomaly_alert: Dict) -> bool:
        """Reinicia serviços dependentes do afetado."""
        service = anomaly_alert.get("executable_path", "unknown")
        logger.info(f"🔄 Reiniciando serviços dependentes de: {service}")

        # Mock: em produção, consultar service mesh para dependências
        await asyncio.sleep(0.4)
        return True

    async def _apply_security_patch(self, anomaly_alert: Dict) -> bool:
        """Aplica patch de segurança crítico."""
        cve_id = anomaly_alert.get("cve_id", "UNKNOWN")
        logger.info(f"🛡️  Aplicando patch de segurança: {cve_id}")

        # Mock: em produção, chamar sistema de patch management
        await asyncio.sleep(0.5)
        return True

    async def _enable_rate_limiting(self, anomaly_alert: Dict) -> bool:
        """Ativa rate limiting emergencial para mitigar ataque."""
        logger.info(f"🚦 Ativando rate limiting emergencial...")

        # Mock: em produção, atualizar config do API gateway
        await asyncio.sleep(0.15)
        return True

    async def _trigger_backup_recovery(self, anomaly_alert: Dict) -> bool:
        """Aciona recuperação de backup para dados corrompidos."""
        logger.info(f"💾 Acionando recuperação de backup...")

        # Mock: em produção, chamar sistema de backup/restore
        await asyncio.sleep(0.6)
        return True

    # Handlers originais (mantidos para compatibilidade)
    async def _restart_service(self, anomaly_alert: Dict) -> bool:
        service_name = anomaly_alert.get("executable_path", "unknown").split("\\")[-1]
        logger.info(f"🔄 Reiniciando serviço: {service_name}")
        await asyncio.sleep(0.5)
        return True

    async def _isolate_process(self, anomaly_alert: Dict) -> bool:
        process_id = anomaly_alert.get("execution_hash", "unknown")
        logger.info(f"🔒 Isolando processo: {process_id}")
        await asyncio.sleep(0.3)
        return True

    async def _flush_memory(self, anomaly_alert: Dict) -> bool:
        logger.info(f"🧹 Liberando memória...")
        await asyncio.sleep(0.2)
        return True

    async def _reset_network(self, anomaly_alert: Dict) -> bool:
        logger.info(f"🌐 Resetando interface de rede...")
        await asyncio.sleep(0.8)
        return True

    async def _restore_registry(self, anomaly_alert: Dict) -> bool:
        logger.info(f"📋 Restaurando registro...")
        await asyncio.sleep(0.6)
        return True

    async def _notify_operator(self, anomaly_alert: Dict) -> bool:
        logger.info(f"📢 Notificando operador sobre alerta {anomaly_alert.get('alert_id')}")
        return True

    async def _trigger_failover(self, anomaly_alert: Dict) -> bool:
        logger.info(f"🔄 Ativando failover para nó secundário...")
        await asyncio.sleep(0.7)
        return True

    async def _rollback_driver(self, anomaly_alert: Dict) -> bool:
        logger.info(f"⬅️  Revertendo driver para versão anterior...")
        await asyncio.sleep(0.5)
        return True

    async def execute_healing(self, anomaly_alert: Dict, action_override: Optional[ExpandedHealingAction] = None) -> Dict:
        """Executa ação de healing para uma anomalia."""
        # Detect feature from alert
        target_feature = None
        for feature in self.FEATURE_HEALING_MAP.keys():
            if feature in anomaly_alert:
                target_feature = feature
                break

        if not target_feature and not action_override:
            logger.warning("Nenhuma feature reconhecida para healing")
            return {"status": "failed", "reason": "no_feature_recognized"}

        # Select first action
        action = action_override if action_override else self.FEATURE_HEALING_MAP[target_feature][0]
        handler = self._action_handlers.get(action)
        if not handler:
             return {"status": "failed", "reason": "handler_not_found"}

        success = await handler(anomaly_alert)
        result = {
            "action": action.value,
            "feature": target_feature,
            "success": success,
            "timestamp": time.time()
        }
        self._healing_history.append(result)
        return result

    def get_expanded_action_catalog(self) -> Dict[str, List[str]]:
        """Retorna catálogo completo de ações mapeadas por feature."""
        return {
            feature: [action.value for action in actions]
            for feature, actions in self.FEATURE_HEALING_MAP.items()
        }

    def get_action_statistics(self) -> Dict:
        """Retorna estatísticas de uso das ações expandidas."""
        from collections import Counter

        action_counts = Counter(
            h.get("action", {}).get("value") if isinstance(h.get("action"), dict) else str(h.get("action"))
            for h in self._healing_history
        )

        return {
            "total_healings": len(self._healing_history),
            "unique_actions_used": len(action_counts),
            "most_used_actions": action_counts.most_common(5),
            "actions_available": len(ExpandedHealingAction),
            "features_mapped": len(self.FEATURE_HEALING_MAP)
        }
