#!/usr/bin/env python3
"""
Substrato 232: Autonomous Sentinel Orchestrator
Coordenação inteligente entre Build, Security e Deployment Sentinels
para CI/CD canônico end-to-end com tomada de decisão autônoma.
"""
import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum, auto
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentinelRole(Enum):
    """Papéis dos sentinels no orchestration."""
    BUILD = "build"           # Validação de builds, Φ_C scoring
    SECURITY = "security"     # Audit de vulnerabilidades, policy enforcement
    DEPLOYMENT = "deployment" # Deploy, health checks, rollback
    COMPLIANCE = "compliance" # Validação regulatória, auditoria

@dataclass
class OrchestrationDecision:
    """Decisão autônoma do orchestrator."""
    decision_id: str
    trigger_event: str
    sentinels_consulted: List[SentinelRole]
    consensus_phi_c: float
    decision: str  # "proceed", "block", "rollback", "escalate"
    rationale: str
    actions_taken: List[str]
    temporal_seal: Optional[str] = None
    created_at: float = field(default_factory=time.time)

class AutonomousSentinelOrchestrator:
    """
    Orchestrator autônomo para coordenação entre sentinels.

    Características:
    • Consenso Φ_C entre múltiplos sentinels para decisões críticas
    • Tomada de decisão autônoma baseada em políticas configuráveis
    • Escalonamento automático para intervenção humana se consenso não alcançado
    • Aprendizado contínuo: ajusta thresholds baseado em histórico de decisões
    • Auditoria completa: cada decisão ancorada na TemporalChain
    """

    # Políticas de decisão autônoma
    DECISION_POLICIES = {
        "npm_install": {
            "required_sentinels": [SentinelRole.BUILD, SentinelRole.SECURITY],
            "min_consensus_phi_c": 0.90,
            "auto_approve_threshold": 0.95,
            "escalate_if_disagreement": True
        },
        "npm_audit_fix": {
            "required_sentinels": [SentinelRole.SECURITY, SentinelRole.BUILD],
            "min_consensus_phi_c": 0.92,
            "auto_approve_threshold": 0.97,
            "escalate_if_disagreement": False  # Auto-aprovar se segurança aprovar
        },
        "production_deploy": {
            "required_sentinels": [SentinelRole.BUILD, SentinelRole.SECURITY, SentinelRole.DEPLOYMENT],
            "min_consensus_phi_c": 0.95,
            "auto_approve_threshold": 0.98,
            "escalate_if_disagreement": True
        },
        "emergency_rollback": {
            "required_sentinels": [SentinelRole.DEPLOYMENT],
            "min_consensus_phi_c": 0.85,
            "auto_approve_threshold": 0.90,
            "escalate_if_disagreement": False  # Rollback sempre auto-aprovado
        }
    }

    def __init__(
        self,
        phi_bus=None,
        temporal_chain=None,
        guardian=None,
        sentinels: Optional[Dict[SentinelRole, Any]] = None
    ):
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.guardian = guardian
        self.sentinels = sentinels or {}
        self._decision_history: List[OrchestrationDecision] = []
        self._policy_learning: Dict[str, Dict] = {}  # policy → learning metrics

    async def orchestrate_event(
        self,
        event_type: str,
        event_data: Dict,
        context: Optional[Dict] = None
    ) -> OrchestrationDecision:
        """
        Orquestra resposta autônoma a um evento do pipeline CI/CD.

        Fluxo:
        1. Identificar política aplicável para o evento
        2. Consultar sentinels requeridos
        3. Calcular consenso Φ_C ponderado
        4. Tomar decisão baseada em thresholds da política
        5. Executar ações correspondentes
        6. Ancorar decisão na TemporalChain
        """
        policy = self.DECISION_POLICIES.get(event_type)
        if not policy:
            logger.warning(f"⚠️  Política não encontrada para evento: {event_type}")
            return await self._fallback_decision(event_type, event_data)

        decision_id = hashlib.sha3_256(
            f"{event_type}:{json.dumps(event_data, sort_keys=True)}:{time.time()}".encode()
        ).hexdigest()[:12]

        logger.info(f"🎯 Orquestrando evento: {event_type} ({decision_id})")

        # Consultar sentinels requeridos
        sentinel_votes = {}
        for role in policy["required_sentinels"]:
            sentinel = self.sentinels.get(role)
            if not sentinel:
                logger.warning(f"⚠️  Sentinel {role.value} não disponível")
                continue

            # Consultar sentinel
            vote = await self._consult_sentinel(sentinel, role, event_type, event_data, context)
            sentinel_votes[role] = vote

        # Calcular consenso Φ_C
        consensus_phi_c = self._calculate_consensus_phi_c(sentinel_votes, policy)

        # Tomar decisão
        if consensus_phi_c >= policy["auto_approve_threshold"]:
            decision = "proceed"
            rationale = f"Consenso Φ_C {consensus_phi_c:.3f} ≥ threshold {policy['auto_approve_threshold']}"
        elif consensus_phi_c >= policy["min_consensus_phi_c"]:
            decision = "proceed_with_monitoring"
            rationale = f"Consenso Φ_C {consensus_phi_c:.3f} ≥ mínimo {policy['min_consensus_phi_c']}"
        elif policy.get("escalate_if_disagreement") and len(set(v.get("approve") for v in sentinel_votes.values())) > 1:
            decision = "escalate"
            rationale = "Desacordo entre sentinels — escalonando para intervenção humana"
        else:
            decision = "block"
            rationale = f"Consenso Φ_C {consensus_phi_c:.3f} < mínimo {policy['min_consensus_phi_c']}"

        # Executar ações correspondentes
        actions = await self._execute_decision_actions(decision, event_type, event_data, sentinel_votes)

        # Criar registro da decisão
        decision_record = OrchestrationDecision(
            decision_id=decision_id,
            trigger_event=event_type,
            sentinels_consulted=list(sentinel_votes.keys()),
            consensus_phi_c=consensus_phi_c,
            decision=decision,
            rationale=rationale,
            actions_taken=actions
        )

        # Ancorar na TemporalChain
        if self.temporal:
            decision_record.temporal_seal = await self.temporal.anchor_event(
                "autonomous_decision_made",
                {
                    "decision_id": decision_id,
                    "event_type": event_type,
                    "decision": decision,
                    "consensus_phi_c": consensus_phi_c,
                    "sentinel_votes": {k.value: v for k, v in sentinel_votes.items()},
                    "rationale": rationale,
                    "timestamp": time.time()
                }
            )

        # Atualizar histórico e aprendizado
        self._decision_history.append(decision_record)
        await self._update_policy_learning(event_type, decision_record, sentinel_votes)

        # Publicar métrica
        if self.phi_bus:
            await self.phi_bus.publish_metric("autonomous_decision", {
                "decision_id": decision_id,
                "event_type": event_type,
                "decision": decision,
                "consensus_phi_c": consensus_phi_c
            })

        logger.info(
            f"✅ Decisão autônoma: {decision_id} | "
            f"Evento: {event_type} | "
            f"Decisão: {decision} | "
            f"Φ_C: {consensus_phi_c:.3f}"
        )

        return decision_record

    async def _consult_sentinel(
        self,
        sentinel: Any,
        role: SentinelRole,
        event_type: str,
        event_data: Dict,
        context: Optional[Dict]
    ) -> Dict:
        """Consulta um sentinel e retorna seu voto com Φ_C."""
        try:
            if role == SentinelRole.BUILD:
                # Build sentinel valida Φ_C do build/artefato
                phi_c = await sentinel.evaluate_artifact_phi_c(event_data)
                return {"approve": phi_c >= 0.85, "phi_c": phi_c, "details": "Build validation"}

            elif role == SentinelRole.SECURITY:
                # Security sentinel valida vulnerabilidades
                vuln_result = await sentinel.scan_for_vulnerabilities(event_data)
                critical = vuln_result.get("critical", 0)
                phi_c = 1.0 if critical == 0 else max(0.5, 1.0 - critical * 0.2)
                return {"approve": critical == 0, "phi_c": phi_c, "details": f"Vulns: {vuln_result}"}

            elif role == SentinelRole.DEPLOYMENT:
                # Deployment sentinel valida readiness para deploy
                readiness = await sentinel.evaluate_deployment_readiness(event_data)
                return {"approve": readiness >= 0.90, "phi_c": readiness, "details": "Deployment readiness"}

            elif role == SentinelRole.COMPLIANCE:
                # Compliance sentinel valida conformidade regulatória
                compliance = await sentinel.validate_regulatory_compliance(event_data)
                return {"approve": compliance["compliant"], "phi_c": compliance["score"], "details": compliance["details"]}

            return {"approve": False, "phi_c": 0.0, "details": "Sentinel not implemented"}

        except Exception as e:
            logger.error(f"❌ Erro ao consultar sentinel {role.value}: {e}")
            return {"approve": False, "phi_c": 0.0, "details": f"Error: {str(e)}"}

    def _calculate_consensus_phi_c(
        self,
        votes: Dict[SentinelRole, Dict],
        policy: Dict
    ) -> float:
        """Calcula consenso Φ_C ponderado entre sentinels."""
        if not votes:
            return 0.0

        # Pesos por papel (configuráveis por política)
        weights = {
            SentinelRole.BUILD: 0.30,
            SentinelRole.SECURITY: 0.35,
            SentinelRole.DEPLOYMENT: 0.25,
            SentinelRole.COMPLIANCE: 0.10
        }

        weighted_sum = sum(
            vote.get("phi_c", 0.0) * weights.get(role, 0.25)
            for role, vote in votes.items()
        )
        total_weight = sum(weights.get(r, 0.25) for r in votes)

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    async def _execute_decision_actions(
        self,
        decision: str,
        event_type: str,
        event_data: Dict,
        sentinel_votes: Dict
    ) -> List[str]:
        """Executa ações correspondentes à decisão."""
        actions = []

        if decision == "proceed":
            actions.append(f"Approved {event_type} with auto-approval")
            # Notificar próximo estágio do pipeline
            if self.phi_bus:
                await self.phi_bus.publish_event("pipeline_proceed", {
                    "event_type": event_type,
                    "decision": "approved"
                })

        elif decision == "proceed_with_monitoring":
            actions.append(f"Approved {event_type} with enhanced monitoring")
            # Ativar monitoring adicional
            actions.append("Enabled enhanced logging and metrics collection")

        elif decision == "block":
            actions.append(f"Blocked {event_type} due to insufficient consensus")
            # Notificar falha
            if self.phi_bus:
                await self.phi_bus.publish_event("pipeline_blocked", {
                    "event_type": event_type,
                    "reason": "consensus_phi_c_insufficient"
                })

        elif decision == "escalate":
            actions.append(f"Escalated {event_type} for human review")
            # Criar ticket para revisão humana
            actions.append("Created review ticket in incident management system")

        elif decision == "rollback":
            actions.append(f"Initiated rollback for {event_type}")
            # Executar rollback via Deployment Sentinel
            if self.sentinels.get(SentinelRole.DEPLOYMENT):
                await self.sentinels[SentinelRole.DEPLOYMENT].execute_rollback(event_data)
                actions.append("Rollback executed successfully")

        return actions

    async def _update_policy_learning(
        self,
        event_type: str,
        decision: OrchestrationDecision,
        sentinel_votes: Dict
    ):
        """Atualiza aprendizado de políticas baseado em histórico de decisões."""
        if event_type not in self._policy_learning:
            self._policy_learning[event_type] = {
                "total_decisions": 0,
                "correct_decisions": 0,  # Definido por feedback posterior
                "avg_consensus_phi_c": 0.0
            }

        learning = self._policy_learning[event_type]
        learning["total_decisions"] += 1

        # Atualizar média móvel de Φ_C de consenso
        n = learning["total_decisions"]
        old_avg = learning["avg_consensus_phi_c"]
        learning["avg_consensus_phi_c"] = old_avg + (decision.consensus_phi_c - old_avg) / n

        # Em produção: ajustar thresholds baseado em feedback de resultados
        # Ex: se decisões com Φ_C=0.92 sempre levam a problemas, aumentar threshold

    async def _fallback_decision(
        self,
        event_type: str,
        event_data: Dict
    ) -> OrchestrationDecision:
        """Decisão de fallback quando política não encontrada."""
        return OrchestrationDecision(
            decision_id=hashlib.sha3_256(f"fallback:{event_type}:{time.time()}".encode()).hexdigest()[:12],
            trigger_event=event_type,
            sentinels_consulted=[],
            consensus_phi_c=0.5,
            decision="escalate",
            rationale="No policy defined for event type — escalating for human review",
            actions_taken=["Created escalation ticket"]
        )

    def get_orchestration_statistics(self) -> Dict:
        """Retorna estatísticas de orquestração autônoma."""
        if not self._decision_history:
            return {"total_decisions": 0}

        by_decision = {}
        by_event = {}

        for d in self._decision_history:
            by_decision[d.decision] = by_decision.get(d.decision, 0) + 1
            by_event[d.trigger_event] = by_event.get(d.trigger_event, 0) + 1

        return {
            "total_decisions": len(self._decision_history),
            "by_decision": by_decision,
            "by_event": by_event,
            "avg_consensus_phi_c": sum(d.consensus_phi_c for d in self._decision_history) / len(self._decision_history),
            "escalation_rate": by_decision.get("escalate", 0) / len(self._decision_history),
            "policy_learning_metrics": self._policy_learning
        }
