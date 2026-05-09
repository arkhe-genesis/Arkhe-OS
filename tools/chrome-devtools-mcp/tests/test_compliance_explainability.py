import pytest
import asyncio
import json
from audit_logger import AuditLogger, DecisionType
from compliance_engine import ComplianceEngine
from compliance_incident_playbook import ComplianceIncidentPlaybook, IncidentSeverity, IncidentType
from explainability_engine import ExplainabilityEngine, ExplanationPersona
from dynamic_consent_protocol import DynamicConsentProtocol, PrivacyProfile

@pytest.mark.asyncio
async def test_full_compliance_flow():
    # 1. Setup
    audit = AuditLogger()
    compliance = ComplianceEngine()
    playbook = ComplianceIncidentPlaybook(audit, compliance)
    explain = ExplainabilityEngine(audit, compliance)
    consent = DynamicConsentProtocol(explain)

    # 2. Log a decision that violates compliance (high bias)
    decision_id = await audit.log_decision(
        decision_type=DecisionType.PROACTIVE_ALERT,
        context={"bias": 0.5, "trigger_metric": "Ω-score", "risk_description": "Test Risk"},
        explainability={"top_features": [("feature1", 0.8)]},
        compliance_tags=["LGPD_art18"],
        expected_impact={"benefit": 0.5, "risk": 0.5}
    )

    record = await audit.get_decision(decision_id)
    compliance_results = compliance.evaluate_compliance(record)

    # LGPD_art18 threshold is 0.3, so bias 0.5 should be False
    assert compliance_results["LGPD_art18"] == False

    # 3. Handle violation with playbook
    incident = await playbook.handle_compliance_violation(
        regulatory_framework="LGPD",
        violated_rule="LGPD_art18",
        context=record.context,
        affected_decision_id=decision_id
    )

    assert incident is not None
    assert incident.incident_type == IncidentType.EXPLAINABILITY_VIOLATION
    assert incident.severity == IncidentSeverity.WARNING
    assert "enhance_explainability_logging" in incident.auto_actions_taken

    # 4. Generate explanation for a citizen
    explanation = await explain.generate_explanation(decision_id, ExplanationPersona.CITIZEN)
    assert "Sua solicitação foi analisada" in explanation.detailed_explanation
    # The order of recourse options is not guaranteed as it comes from a set
    assert any("LGPD" in opt or "ANPD" in opt for opt in explanation.recourse_options)

    # 5. Dynamic Consent Adaptation
    consent.set_citizen_profile("cit_123", PrivacyProfile.CONSERVATIVE, {"analytics": False})
    persona = consent.get_adapted_persona("cit_123")
    assert persona == ExplanationPersona.CITIZEN

    consent.set_citizen_profile("cit_456", PrivacyProfile.OPEN, {"analytics": True})
    persona = consent.get_adapted_persona("cit_456")
    assert persona == ExplanationPersona.TECHNICAL

    # 6. Validate action based on consent
    assert consent.validate_action("cit_123", "analytics") == False
    assert consent.validate_action("cit_456", "analytics") == True

@pytest.mark.asyncio
async def test_fs55_notification_and_portability():
    from proactive_notifications import ProactiveNotificationEngine, NotificationChannel
    from data_portability import DataPortabilityEngine, ExportFormat

    audit = AuditLogger()
    explain = ExplainabilityEngine(audit, ComplianceEngine())
    consent = DynamicConsentProtocol(explain)
    notify = ProactiveNotificationEngine(consent, audit)
    portability = DataPortabilityEngine(audit)

    citizen_id = "cit_FS55"
    consent.set_citizen_profile(citizen_id, PrivacyProfile.BALANCED, {"notifications": True})

    # Mock channel handler
    async def mock_handler(msg): return True
    notify.register_channel_handler(NotificationChannel.IN_APP, mock_handler)

    # 1. Decision and Notification
    decision_id = await audit.log_decision(DecisionType.PROACTIVE_ALERT, {"citizen_id": citizen_id}, {}, [], {})
    record = await audit.get_decision(decision_id)

    await notify.process_decision(record, citizen_id)
    assert len(notify.delivery_log) == 1
    assert notify.delivery_log[0].citizen_id == citizen_id

    # 2. Portability Export
    package = await portability.request_export(citizen_id, ExportFormat.JSON_LD)
    assert package.citizen_id == citizen_id
    assert "decisions" in package.content
    assert package.signature.startswith("sig_cathedral_")

@pytest.mark.asyncio
async def test_crypto_shredding():
    from crypto_shredding import CryptoShreddingSystem
    shredder = CryptoShreddingSystem()
    cid = "cit_shred"

    key = shredder.generate_citizen_key(cid)
    assert shredder.get_citizen_key(cid) == key

    shredder.request_shredding(cid)
    assert shredder.get_citizen_key(cid) is None
    assert shredder.is_shredded(cid) == True

@pytest.mark.asyncio
async def test_cross_jurisdiction_audit():
    from cross_jurisdiction_audit import CrossJurisdictionAuditor
    audit = AuditLogger()
    cj_auditor = CrossJurisdictionAuditor(audit)

    decision_id = await audit.log_decision(DecisionType.RECOVERY_ACTION, {"secret": "data"}, {}, ["LGPD_art18"], {})
    record = await audit.get_decision(decision_id)

    proof = await cj_auditor.generate_audit_proof(decision_id, "EU")
    assert proof["jurisdiction"] == "EU"
    assert "secret" not in json.dumps(proof)
    assert proof["merkle_root_anchor"] == record.merkle_root

    assert cj_auditor.verify_remote_proof(proof, record.merkle_root) == True

@pytest.mark.asyncio
async def test_audit_integrity():
    audit = AuditLogger()
    decision_id = await audit.log_decision(
        decision_type=DecisionType.MANUAL_OVERRIDE,
        context={},
        explainability={},
        compliance_tags=[],
        expected_impact={}
    )
    record = await audit.get_decision(decision_id)
    assert record.merkle_root is not None
    assert record.signature.startswith("sig_")
