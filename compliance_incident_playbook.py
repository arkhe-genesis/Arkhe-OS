# compliance_incident_playbook.py — Resposta automatizada a violações de conformidade

import asyncio
import time
import json
import logging
import hashlib
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timedelta

from audit_logger import AuditLogger, DecisionType, AuditRecord
from compliance_engine import ComplianceEngine


class IncidentSeverity(Enum):
    """Níveis de severidade de incidentes regulatórios."""
    OBSERVATION = auto()    # Nível 1: registro e observação
    WARNING = auto()        # Nível 2: mitigação em 24h
    CRITICAL = auto()       # Nível 3: ação em <1h, notificação regulatória
    EMERGENCY = auto()      # Nível 4: rollback imediato, isolamento


class IncidentType(Enum):
    """Tipos de violações de conformidade."""
    EXPLAINABILITY_VIOLATION = auto()    # Decisão sem explicação adequada
    HUMAN_APPROVAL_MISSING = auto()       # Ação crítica sem aprovação humana
    PRIVACY_BREACH = auto()               # Vazamento ou uso indevido de PII
    MODEL_GOVERNANCE = auto()             # Modelo promovido sem validação
    RETENTION_VIOLATION = auto()          # Dados retidos além do permitido
    AUDIT_CHAIN_BROKEN = auto()           # Hash chain corrompida ou incompleta


@dataclass
class ComplianceIncident:
    """Registro de um incidente de conformidade."""
    incident_id: str
    timestamp: float
    severity: IncidentSeverity
    incident_type: IncidentType
    regulatory_framework: str  # "LGPD", "GDPR", "ISO27001", etc.
    violated_rule: str  # ex: "LGPD_art18", "GDPR_art22"
    description: str
    affected_resources: List[str]  # decisões, modelos, dados afetados
    evidence_snapshot_hash: str  # hash dos dados coletados
    auto_actions_taken: List[str] = field(default_factory=list)
    human_escalation_required: bool = False
    resolved: bool = False
    resolution_timestamp: Optional[float] = None


@dataclass
class IncidentResponseAction:
    """Ação automatizada de resposta a incidente."""
    action_id: str
    name: str
    description: str
    applicable_severities: List[IncidentSeverity]
    applicable_types: List[IncidentType]
    execute_func: Callable[[ComplianceIncident], bool]
    rollback_func: Optional[Callable[[ComplianceIncident], bool]] = None
    evidence_required: bool = True

# Mocks for functions referenced in the actions
def enable_detailed_explainability_logging(resources):
    logging.info(f"Detailed explainability logging enabled for {resources}")
    return True

def flag_for_human_review(resources):
    logging.info(f"Flagged for human review: {resources}")
    return True

def execute_rollback_for_unapproved(resources):
    logging.info(f"Rolling back unapproved action for {resources}")
    return True

def restore_pre_rollback_state(resources):
    logging.info(f"Restoring pre-rollback state for {resources}")
    return True

def enable_approval_gateway(framework):
    logging.info(f"Approval gateway enabled for {framework}")
    return True

def quarantine_pii_data(resources):
    logging.info(f"Quarantining PII data: {resources}")
    return True

def send_regulatory_notification(incident):
    logging.info(f"Regulatory notification sent for {incident.incident_id}")
    return True


class ComplianceIncidentPlaybook:
    """
    Playbook de resposta automatizada a incidentes regulatórios.
    Integra detecção, classificação, ação e aprendizado.
    """

    # Catálogo de ações de resposta por tipo e severidade
    RESPONSE_ACTIONS: Dict[IncidentType, List[IncidentResponseAction]] = {
        IncidentType.EXPLAINABILITY_VIOLATION: [
            IncidentResponseAction(
                action_id="enhance_explainability_logging",
                name="Aumentar logging de explicabilidade",
                description="Ativa logging detalhado para decisões futuras do mesmo tipo",
                applicable_severities=[IncidentSeverity.OBSERVATION, IncidentSeverity.WARNING],
                applicable_types=[IncidentType.EXPLAINABILITY_VIOLATION],
                execute_func=lambda inc: enable_detailed_explainability_logging(inc.affected_resources),
                evidence_required=True
            ),
            IncidentResponseAction(
                action_id="require_human_review",
                name="Exigir revisão humana para decisões similares",
                description="Marca decisões futuras do mesmo tipo para aprovação humana",
                applicable_severities=[IncidentSeverity.WARNING, IncidentSeverity.CRITICAL],
                applicable_types=[IncidentType.EXPLAINABILITY_VIOLATION],
                execute_func=lambda inc: flag_for_human_review(inc.affected_resources),
                evidence_required=True
            ),
        ],
        IncidentType.HUMAN_APPROVAL_MISSING: [
            IncidentResponseAction(
                action_id="rollback_unapproved_action",
                name="Reverter ação não aprovada",
                description="Executa rollback da ação que faltou aprovação humana",
                applicable_severities=[IncidentSeverity.CRITICAL, IncidentSeverity.EMERGENCY],
                applicable_types=[IncidentType.HUMAN_APPROVAL_MISSING],
                execute_func=lambda inc: execute_rollback_for_unapproved(inc.affected_resources),
                rollback_func=lambda inc: restore_pre_rollback_state(inc.affected_resources),
                evidence_required=True
            ),
            IncidentResponseAction(
                action_id="enforce_approval_gateway",
                name="Ativar gateway de aprovação obrigatória",
                description="Bloqueia execuções futuras sem aprovação humana explícita",
                applicable_severities=[IncidentSeverity.WARNING, IncidentSeverity.CRITICAL],
                applicable_types=[IncidentType.HUMAN_APPROVAL_MISSING],
                execute_func=lambda inc: enable_approval_gateway(inc.regulatory_framework),
                evidence_required=False
            ),
        ],
        IncidentType.PRIVACY_BREACH: [
            IncidentResponseAction(
                action_id="isolate_affected_data",
                name="Isolar dados afetados",
                description="Marca dados PII afetados como quarentena, bloqueia acesso",
                applicable_severities=[IncidentSeverity.CRITICAL, IncidentSeverity.EMERGENCY],
                applicable_types=[IncidentType.PRIVACY_BREACH],
                execute_func=lambda inc: quarantine_pii_data(inc.affected_resources),
                evidence_required=True
            ),
            IncidentResponseAction(
                action_id="notify_dpo_and_regulator",
                name="Notificar DPO e regulador",
                description="Envia notificação formal conforme prazos regulatórios",
                applicable_severities=[IncidentSeverity.CRITICAL, IncidentSeverity.EMERGENCY],
                applicable_types=[IncidentType.PRIVACY_BREACH],
                execute_func=lambda inc: send_regulatory_notification(inc),
                evidence_required=True
            ),
        ],
    }

    # Mapeamento: violação regulatória → tipo de incidente e severidade inicial
    VIOLATION_TO_INCIDENT = {
        "LGPD_art18": (IncidentType.EXPLAINABILITY_VIOLATION, IncidentSeverity.WARNING),
        "GDPR_art22": (IncidentType.HUMAN_APPROVAL_MISSING, IncidentSeverity.CRITICAL),
        "ISO27001_A.12.4": (IncidentType.AUDIT_CHAIN_BROKEN, IncidentSeverity.CRITICAL),
        "LGPD_art46": (IncidentType.PRIVACY_BREACH, IncidentSeverity.EMERGENCY),
    }

    def __init__(
        self,
        audit_logger: AuditLogger,
        compliance_engine: ComplianceEngine,
        rollback_orchestrator: Any = None
    ):
        self.audit = audit_logger
        self.compliance = compliance_engine
        self.rollback = rollback_orchestrator

        self.active_incidents: Dict[str, ComplianceIncident] = {}
        self.resolved_incidents: List[ComplianceIncident] = []
        self._notification_callbacks: List[Callable] = []

    async def handle_compliance_violation(
        self,
        regulatory_framework: str,
        violated_rule: str,
        context: Dict[str, Any],
        affected_decision_id: Optional[str] = None
    ) -> Optional[ComplianceIncident]:
        """
        Processa uma violação de conformidade detectada pelo ComplianceEngine.
        Retorna incidente criado ou None se ignorado.
        """
        # Mapeia violação para tipo e severidade de incidente
        if violated_rule not in self.VIOLATION_TO_INCIDENT:
            logging.warning(f"[COMPLIANCE] Violação não mapeada: {violated_rule}")
            return None

        incident_type, initial_severity = self.VIOLATION_TO_INCIDENT[violated_rule]

        # Coleta evidências automáticas
        evidence_hash = await self._collect_incident_evidence(
            regulatory_framework, violated_rule, context, affected_decision_id
        )

        # Cria incidente
        incident = ComplianceIncident(
            incident_id=f"inc_{int(time.time() * 1e6)}",
            timestamp=time.time(),
            severity=initial_severity,
            incident_type=incident_type,
            regulatory_framework=regulatory_framework,
            violated_rule=violated_rule,
            description=f"Violação de {violated_rule} em {regulatory_framework}",
            affected_resources=[affected_decision_id] if affected_decision_id else [],
            evidence_snapshot_hash=evidence_hash
        )

        # Registra no AuditLedger
        await self.audit.log_decision(
            decision_type=DecisionType.MANUAL_OVERRIDE,  # Reuso para incidentes
            context={
                "incident_id": incident.incident_id,
                "type": incident_type.name,
                "severity": initial_severity.name,
                "rule": violated_rule
            },
            explainability={"natural_language": incident.description},
            compliance_tags=[f"{regulatory_framework}_{violated_rule}"],
            expected_impact={"risk": 0.8 if initial_severity in [IncidentSeverity.CRITICAL, IncidentSeverity.EMERGENCY] else 0.3}
        )

        # Executa ações automatizadas baseadas em severidade e tipo
        await self._execute_response_actions(incident)

        # Notifica canais apropriados
        await self._notify_incident(incident)

        # Registra incidente ativo
        self.active_incidents[incident.incident_id] = incident

        logging.critical(f"[INCIDENT] Incidente criado: {incident.incident_id} ({incident.severity.name})")
        return incident

    async def _collect_incident_evidence(
        self,
        framework: str,
        rule: str,
        context: Dict,
        decision_id: Optional[str]
    ) -> str:
        """Coleta e hashea evidências do incidente."""
        evidence = {
            "timestamp": time.time(),
            "framework": framework,
            "rule": rule,
            "context": context,
            "decision_record": None
        }

        # Se há decisão afetada, recupera registro do AuditLedger
        if decision_id:
            decision_record = await self.audit.get_decision(decision_id)
            if decision_record:
                evidence["decision_record"] = {
                    "decision_id": decision_record.decision_id,
                    "decision_type": decision_record.decision_type.name,
                    "explainability": decision_record.explainability,
                    "compliance_tags": decision_record.compliance_tags
                }

        # Gera hash SHA-256 do snapshot de evidências
        evidence_json = json.dumps(evidence, sort_keys=True, default=str)
        return hashlib.sha256(evidence_json.encode()).hexdigest()

    async def _execute_response_actions(self, incident: ComplianceIncident):
        """Executa ações de resposta automatizadas para o incidente."""
        actions = self.RESPONSE_ACTIONS.get(incident.incident_type, [])

        for action in actions:
            # Verifica se ação é aplicável à severidade atual
            if incident.severity not in action.applicable_severities:
                continue

            try:
                logging.info(f"[INCIDENT] Executando ação: {action.name} para {incident.incident_id}")
                success = action.execute_func(incident)

                if success:
                    incident.auto_actions_taken.append(action.action_id)

                    # Se ação requer evidência, atualiza hash
                    if action.evidence_required:
                        incident.evidence_snapshot_hash = await self._collect_incident_evidence(
                            incident.regulatory_framework,
                            incident.violated_rule,
                            {"action_executed": action.action_id},
                            incident.affected_resources[0] if incident.affected_resources else None
                        )

                    # Se ação resolve o incidente, marca como resolvido
                    if incident.severity == IncidentSeverity.OBSERVATION:
                        await self._resolve_incident(incident, "Ação de observação executada com sucesso")
                else:
                    logging.error(f"[INCIDENT] Falha na ação {action.action_id}")
                    incident.human_escalation_required = True

            except Exception as e:
                logging.exception(f"[INCIDENT] Exceção na ação {action.action_id}: {e}")
                incident.human_escalation_required = True

        # Se incidente é crítico/emergência e ações falharam, escala para humano
        if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.EMERGENCY] and incident.human_escalation_required:
            await self._escalate_to_human(incident)

    async def _notify_incident(self, incident: ComplianceIncident):
        """Notifica canais apropriados sobre o incidente."""
        # Determina canais baseado em severidade e framework
        channels = []
        if incident.severity == IncidentSeverity.OBSERVATION:
            channels = ["internal_log"]
        elif incident.severity == IncidentSeverity.WARNING:
            channels = ["dpo_email", "slack_compliance"]
        elif incident.severity == IncidentSeverity.CRITICAL:
            channels = ["dpo_email", "regulator_api", "pagerduty_critical"]
        elif incident.severity == IncidentSeverity.EMERGENCY:
            channels = ["dpo_email", "regulator_api", "pagerduty_emergency", "executive_sms"]

        # Monta mensagem
        message = f"""
🚨 INCIDENTE DE CONFORMIDADE DETECTADO
ID: {incident.incident_id}
Framework: {incident.regulatory_framework}
Regra Violada: {incident.violated_rule}
Severidade: {incident.severity.name}
Descrição: {incident.description}
Ações Automáticas: {', '.join(incident.auto_actions_taken) if incident.auto_actions_taken else 'Nenhuma'}
Evidência Hash: {incident.evidence_snapshot_hash[:16]}...
Timestamp: {datetime.fromtimestamp(incident.timestamp).isoformat()}
"""
        if incident.human_escalation_required:
            message += "\n⚠️ ESCALADO PARA REVISÃO HUMANA"

        # Envia para canais
        for channel in channels:
            callback = next((cb for cb in self._notification_callbacks if getattr(cb, '__name__', '') == channel), None)
            if callback:
                await callback(message, incident)
            else:
                logging.info(f"[INCIDENT] Notificação simulada para {channel}: {message[:200]}...")

    async def _escalate_to_human(self, incident: ComplianceIncident):
        """Escala incidente para revisão humana urgente."""
        logging.critical(f"[INCIDENT] Escalando para humano: {incident.incident_id}")

        # Notifica equipe de plantão
        await self._notify_incident(incident)  # Reutiliza notificação com canais de emergência

        # Atualiza incidente
        incident.human_escalation_required = True

    async def _resolve_incident(self, incident: ComplianceIncident, resolution_note: str):
        """Marca incidente como resolvido e registra resolução."""
        incident.resolved = True
        incident.resolution_timestamp = time.time()

        # Registra resolução no AuditLedger
        await self.audit.log_decision(
            decision_type=DecisionType.MANUAL_OVERRIDE,
            context={
                "incident_id": incident.incident_id,
                "resolution_note": resolution_note,
                "actions_taken": incident.auto_actions_taken
            },
            explainability={"natural_language": f"Incidente resolvido: {resolution_note}"},
            compliance_tags=[f"{incident.regulatory_framework}_resolved"],
            expected_impact={"risk": 0.0}
        )

        # Move de ativos para resolvidos
        if incident.incident_id in self.active_incidents:
            del self.active_incidents[incident.incident_id]
        self.resolved_incidents.append(incident)

        logging.info(f"[INCIDENT] Incidente resolvido: {incident.incident_id} — {resolution_note}")

    def register_notification_callback(self, callback: Callable, channel_name: str):
        """Registra callback para notificação em canal específico."""
        callback.__name__ = channel_name  # Hack para identificação
        self._notification_callbacks.append(callback)
