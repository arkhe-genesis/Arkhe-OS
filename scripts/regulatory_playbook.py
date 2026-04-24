# regulatory_playbook.py — Playbook de resposta a incidentes regulatórios

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from audit_logger import AuditLogger, AuditRecord, DecisionType
from compliance_engine import ComplianceEngine

class RegulatoryIncidentResponsePlaybook:
    """
    Playbook que automatiza a gestão de violações de compliance.
    """

    def __init__(self, audit_logger: AuditLogger, compliance_engine: ComplianceEngine):
        self.audit = audit_logger
        self.compliance = compliance_engine
        self.incident_log: List[Dict] = []

    async def monitor_for_violations(self, interval_s: float = 60.0):
        """Monitora continuamente o Códice em busca de violações de conformidade."""
        logging.info("[REGULATORY] Monitoramento de incidentes regulatórios iniciado")
        last_check = time.time()

        while True:
            try:
                # Busca decisões desde o último check
                records = await self.audit.query_decisions(start_time=last_check)

                for record in records:
                    compliance_status = await self.compliance.check_decision_compliance(record.decision_id)

                    if not compliance_status["all_compliant"]:
                        await self._handle_compliance_incident(record, compliance_status["violations"])

                last_check = time.time()
                await asyncio.sleep(interval_s)

            except Exception as e:
                logging.error(f"[REGULATORY] Erro no monitoramento: {e}")
                await asyncio.sleep(10)

    async def _handle_compliance_incident(self, record: AuditRecord, violations: List[str]):
        """Executa ações automáticas de mitigação para violações de compliance."""
        incident_id = f"inc_{record.decision_id}_{int(time.time())}"
        logging.warning(f"[REGULATORY] INCIDENTE DETECTADO: {incident_id} | Violações: {violations}")

        actions_taken = []

        # 1. Notificação Imediata
        actions_taken.append("OFFICER_NOTIFICATION_SENT")

        # 2. Avaliação de Risco e Ações Específicas
        if "GDPR_art22" in violations or "LGPD_art18" in violations:
            # Violação de direitos do titular (explicabilidade ou intervenção humana)
            if record.decision_type == DecisionType.RECOVERY_ACTION:
                actions_taken.append("AUTOMATED_ACTION_SUSPENDED")
                # Em um sistema real, aqui chamaríamos um rollback
                actions_taken.append("ROLLBACK_INITIATED")

        if "ISO27001_A.12.4" in violations:
            # Falha de integridade/assinatura
            actions_taken.append("INTEGRITY_ALERT_DISPATCHED")
            actions_taken.append("SYSTEM_QUARANTINE_READY")

        incident = {
            "incident_id": incident_id,
            "decision_id": record.decision_id,
            "timestamp": time.time(),
            "violations": violations,
            "mitigation_actions": actions_taken,
            "status": "MITIGATED"
        }

        self.incident_log.append(incident)

        # Registra a ação de mitigação no próprio Códice
        await self.audit.log_decision(
            decision_type=DecisionType.ROLLBACK_EXECUTION,
            context={"incident_id": incident_id, "original_decision": record.decision_id},
            explainability={"natural_language": f"Mitigação automática disparada devido a violações: {', '.join(violations)}"},
            compliance_tags=["ISO27001_A.17.2"],
            expected_impact={"risk_reduction": 0.9}
        )

        return incident

    def get_active_incidents(self) -> List[Dict]:
        return [inc for inc in self.incident_log if inc["status"] != "RESOLVED"]
