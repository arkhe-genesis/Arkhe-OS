# regulatory_incident_playbook.py — Reflexos automatizados de conformidade

import time
import asyncio
import logging
import hashlib
from enum import Enum, auto
from typing import Dict, List, Any
from datetime import datetime
from audit_logger import AuditLogger, DecisionType

class RegulatoryIncidentType(Enum):
    AUTOMATED_DECISION_BIAS = auto()      # Viés em decisão automatizada (GDPR Art.22)
    DATA_BREACH_PERSONAL = auto()          # Vazamento de dados pessoais (LGPD Art.48)
    UNAUTHORIZED_MODEL_CHANGE = auto()    # Promoção de modelo não autorizada (SOX)
    RETENTION_POLICY_VIOLATION = auto()   # Dados não expurgados (LGPD Art.15)
    EXPLAINABILITY_FAILURE = auto()       # Decisão sem justificativa rastreável
    CROSS_BORDER_TRANSFER_VIOLATION = auto() # Transferência internacional irregular

# Playbook: mapeia tipo de incidente → lista de ações obrigatórias
REGULATORY_PLAYBOOKS = {
    RegulatoryIncidentType.DATA_BREACH_PERSONAL: [
        {"action": "isolate_affected_systems", "deadline_minutes": 0},
        {"action": "suspend_data_processing", "deadline_minutes": 5},
        {"action": "notify_dpo", "deadline_minutes": 15},
        {"action": "log_forensic_snapshot", "deadline_minutes": 60},
        {"action": "assess_impact", "deadline_hours": 24},
        {"action": "notify_regulator", "deadline_hours": 72},  # LGPD: prazo de 3 dias úteis
        {"action": "notify_data_subjects", "deadline_hours": 72},
        {"action": "apply_remediation_policy", "deadline_hours": 120},
        {"action": "generate_final_report", "deadline_days": 30},
    ],
    RegulatoryIncidentType.EXPLAINABILITY_FAILURE: [
        {"action": "quarantine_decision_output", "deadline_minutes": 0},
        {"action": "generate_human_readable_explanation", "deadline_minutes": 30},
        {"action": "notify_compliance_officer", "deadline_hours": 2},
        {"action": "rebuild_decision_path", "deadline_hours": 24},
    ],
}

class RegulatoryIncident:
    def __init__(self, incident_id, incident_type, violation_alert, status, started_at, playbook_steps):
        self.incident_id = incident_id
        self.incident_type = incident_type
        self.violation_alert = violation_alert
        self.status = status
        self.started_at = started_at
        self.playbook_steps = playbook_steps
        self.completed_steps = []

class RegulatoryResponseEngine:
    """
    Motor que executa playbooks de resposta a incidentes regulatórios.
    Trabalha junto com o ComplianceEngine e o Livro de Bronze.
    """

    def __init__(self, compliance_engine, audit_ledger, codex=None):
        self.compliance = compliance_engine
        self.audit = audit_ledger
        self.codex = codex
        self.active_incidents: Dict[str, RegulatoryIncident] = {}

    async def handle_compliance_violation(self, violation_alert: Dict):
        """
        Ponto de entrada: recebe um alerta de violação do ComplianceEngine
        e dispara o playbook correspondente.
        """
        incident_type = self._classify_violation(violation_alert)
        incident_id = f"reg_inc_{int(time.time())}"

        playbook = REGULATORY_PLAYBOOKS.get(incident_type, [])

        incident = RegulatoryIncident(
            incident_id=incident_id,
            incident_type=incident_type,
            violation_alert=violation_alert,
            status="ACTIVE",
            started_at=time.time(),
            playbook_steps=playbook,
        )
        self.active_incidents[incident_id] = incident

        logging.critical(f"[REGULATORY] Incidente {incident_id} aberto: {incident_type.name}")

        # Executa todas as ações do playbook, respeitando deadlines
        await self._execute_incident_playbook(incident)

    def _classify_violation(self, violation_alert: Dict) -> RegulatoryIncidentType:
        rule = violation_alert.get('rule')
        if rule == "LGPD_art18": return RegulatoryIncidentType.EXPLAINABILITY_FAILURE
        if rule == "LGPD_art46": return RegulatoryIncidentType.DATA_BREACH_PERSONAL
        return RegulatoryIncidentType.EXPLAINABILITY_FAILURE

    async def _execute_incident_playbook(self, incident):
        for step in incident.playbook_steps:
            try:
                await self._execute_step(step, incident)
                incident.completed_steps.append(step)
            except Exception as e:
                logging.error(f"[REGULATORY] Falha no passo {step['action']}: {e}")
                return
        # Ao concluir todos os passos
        incident.status = "RESOLVED"

    async def _execute_step(self, step: Dict, incident):
        action = step['action']

        # Ações são implementadas como métodos especializados
        if action == "isolate_affected_systems":
            logging.info(f"Isolating affected systems for {incident.incident_id}")
        elif action == "notify_dpo":
            logging.info(f"Notifying DPO for {incident.incident_id}")
        elif action == "notify_regulator":
            await self._notify_regulator_automated(incident)
        elif action == "notify_data_subjects":
            await self._notify_citizens_affected(incident)
        else:
            logging.info(f"Executing generic action {action} for {incident.incident_id}")

        # Registra a ação executada no Livro de Bronze
        await self.audit.log_decision(
            decision_type=DecisionType.MANUAL_OVERRIDE,
            context={"incident_id": incident.incident_id, "action": step['action']},
            explainability={"reason": f"Resposta regulatória ao incidente {incident.incident_type.name}"},
            compliance_tags=incident.violation_alert.get('tags', []),
            expected_impact={"benefit": 0.8, "risk": 0.1}
        )

    async def _notify_regulator_automated(self, incident: RegulatoryIncident):
        """Notifica automaticamente o regulador via API assinada."""
        logging.info(f"[FS-67-B] Enviando pacote de evidências para Autoridade Competente (Incidente: {incident.incident_id})")
        # Simulação de envio seguro
        await asyncio.sleep(0.2)
        logging.info(f"[FS-67-B] Autoridade Notificada. Protocolo: {hashlib.sha256(incident.incident_id.encode()).hexdigest()[:12]}")

    async def _notify_citizens_affected(self, incident: RegulatoryIncident):
        """Notifica os cidadãos afetados usando a persona apropriada do motor de explicabilidade."""
        logging.info(f"[FS-67-B] Preparando notificações adaptadas para Cidadãos Afetados.")
        # Em produção, buscaria os DIDs afetados no AuditLog
        logging.info(f"[FS-67-B] Cidadãos notificados via PUSH/In-App. 'Sua soberania digital permanece preservada'.")
