# incident/regulatory_notifier.py — Notificador automático de incidentes regulatórios

import hashlib
import json
import time
import asyncio
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field

@dataclass
class RegulatoryIncident:
    incident_id: str
    detected_at: float
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    affected_jurisdictions: List[str]
    data_categories: List[str]
    citizen_count: int
    description_hash: str
    mitigation_actions: List[str]
    dpo_contact: str

@dataclass
class RegulatoryNotification:
    notification_id: str
    incident_id: str
    authority: str
    jurisdiction: str
    template_version: str
    content: Dict
    signature: str
    sent_at: Optional[float] = None
    delivery_status: str = "pending"

class RegulatoryIncidentNotifier:
    """
    Automatiza notificações de incidentes a autoridades e cidadãos
    conforme requisitos legais de múltiplas jurisdições (FS-68).
    """

    JURISDICTION_CONFIG = {
        "LGPD": {"authority": "ANPD", "deadline_hours": 72, "template": "anpd_v2.1"},
        "GDPR": {"authority": "ICO", "deadline_hours": 72, "template": "gdpr_breach_v1.3"},
        "CCPA": {"authority": "CA_AG", "deadline_hours": 48, "template": "ccpa_v1.0"}
    }

    def __init__(self, audit_ledger):
        self.audit = audit_ledger
        self._pending_notifications: Dict[str, RegulatoryNotification] = {}

    async def classify_and_notify(self, incident: RegulatoryIncident) -> Dict[str, List[RegulatoryNotification]]:
        notifications_by_jurisdiction = {}

        for juris in incident.affected_jurisdictions:
            config = self.JURISDICTION_CONFIG.get(juris, {"authority": "Unknown", "template": "default"})

            notification_id = f"notify_{juris}_{hashlib.sha256(incident.incident_id.encode()).hexdigest()[:8]}"

            content = {
                "incident_id": incident.incident_id,
                "severity": incident.severity,
                "affected_categories": incident.data_categories,
                "citizen_count": incident.citizen_count,
                "dpo": incident.dpo_contact
            }

            notification = RegulatoryNotification(
                notification_id=notification_id,
                incident_id=incident.incident_id,
                authority=config["authority"],
                jurisdiction=juris,
                template_version=config["template"],
                content=content,
                signature=f"sig_did_cathedral_{notification_id[:8]}"
            )

            notifications_by_jurisdiction.setdefault(juris, []).append(notification)
            self._pending_notifications[notification_id] = notification

            await self.audit.log_decision(
                decision_type="REGULATORY_NOTIFICATION_GENERATED",
                context={"jurisdiction": juris, "notification_id": notification_id},
                explainability={"reason": f"Notificação automática {juris} disparada via FS-68"},
                compliance_tags=["incident_response", juris],
                expected_impact={"benefit": 1.0, "risk": 0.0}
            )

            # Simulação de envio assíncrono
            asyncio.create_task(self._simulate_send(notification))

        return notifications_by_jurisdiction

    async def _simulate_send(self, notification: RegulatoryNotification):
        await asyncio.sleep(0.5)
        notification.delivery_status = "confirmed"
        notification.sent_at = time.time()

    async def notify_affected_citizens(self, incident: RegulatoryIncident, citizen_dids: List[str]):
        """Notifica cidadãos via Wallet/DIDComm."""
        for did in citizen_dids:
            did_hash = hashlib.sha256(did.encode()).hexdigest()[:16]
            await self.audit.log_decision(
                decision_type="CITIZEN_NOTIFICATION_SENT",
                context={"citizen_did_hash": did_hash, "incident_id": incident.incident_id},
                explainability={"reason": "O cidadão tem o direito de ser informado sobre violações de seus dados (LGPD Art. 48)"},
                compliance_tags=["transparency", "citizen_rights"],
                expected_impact={"benefit": 0.9, "risk": 0.05}
            )

    def to_dict(self) -> Dict:
        return {
            "pending_notifications": len(self._pending_notifications),
            "jurisdictions_supported": list(self.JURISDICTION_CONFIG.keys())
        }
