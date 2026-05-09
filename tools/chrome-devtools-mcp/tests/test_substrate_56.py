# tests/test_substrate_56.py
import asyncio
import pytest
import json
from catedrald_part2 import CatedralCore
from dynamic_consent_protocol import DataCategory, PrivacyProfile, Purpose
from cross_jurisdiction_audit import AuditQuery

@pytest.fixture
def core():
    return CatedralCore()

@pytest.mark.asyncio
async def test_crypto_shredding(core):
    citizen_id = "cit_123"
    # Execute shredding
    attestation = await core.shredder.execute_shredding(citizen_id)
    assert attestation.citizen_id_hash is not None
    assert len(attestation.key_ids) > 0

    # Verify shredding
    success = await core.shredder.verify_shredding(attestation)
    assert success is True

    # Check audit log
    logs = core.immune.get_audit_log()
    assert any(log['action'] == "CRYPTO_SHRED_EXECUTED" for log in logs)

@pytest.mark.asyncio
async def test_granular_consent_matrix(core):
    citizen_id = "cit_456"

    # Default BALANCED profile: Biometric denied even for research in balanced?
    # Our logic: RESEARCH allowed if NOT (BIOMETRIC, HEALTH, FINANCIAL)
    assert core.consent.is_allowed(citizen_id, DataCategory.BIOMETRIC, Purpose.RESEARCH) is False
    assert core.consent.is_allowed(citizen_id, DataCategory.LOCATION, Purpose.RESEARCH) is True

    # Essential purposes should be allowed in balanced
    assert core.consent.is_allowed(citizen_id, DataCategory.BIOMETRIC, Purpose.SECURITY) is True

    # Update to CONSERVATIVE
    core.consent.update_profile(citizen_id, PrivacyProfile.CONSERVATIVE)
    assert core.consent.is_allowed(citizen_id, DataCategory.LOCATION, Purpose.RESEARCH) is False
    assert core.consent.is_allowed(citizen_id, DataCategory.LOCATION, Purpose.SECURITY) is True # Essential

    # Granular update
    core.consent.update_entry(citizen_id, DataCategory.FINANCIAL, Purpose.MARKETING, True)
    assert core.consent.is_allowed(citizen_id, DataCategory.FINANCIAL, Purpose.MARKETING) is True

@pytest.mark.asyncio
async def test_cross_jurisdiction_audit(core):
    # Record some events
    await core.immune.record_event(event_type="DECISION", decision="ALLOW", bias=0.2)
    await core.immune.record_event(event_type="DECISION", decision="DENY", bias=0.8)

    query = AuditQuery(
        id="q_1",
        framework="GDPR",
        article="22",
        start_time=0,
        end_time=9999999999,
        predicate=lambda e: e.get('details', {}).get('bias', 0) < 0.5
    )

    proof = await core.auditor.handle_audit_query(query)
    assert proof.compliant_count == 1
    assert proof.total_events_in_period >= 2
    assert len(proof.proofs) == 1
    assert proof.merkle_root is not None

@pytest.mark.asyncio
async def test_universal_portability_json_ld(core):
    citizen_id = "cit_789"
    data = {
        "biometrics": {"fingerprint": "xyz"},
        "location": {"lat": 10, "lng": 20},
        "public_info": {"name": "Cid"}
    }

    # Balanced profile: Location allowed for Service, Biometric allowed for Service
    # Wait, in BALANCED, essential_purposes include SERVICE_PROVISION.
    # So both should be allowed if they are essential.

    export = core.portability.export_data(citizen_id, data, core.consent)

    assert "@context" in export
    assert export["@type"] == "CitizenData"
    assert "location" in export["payload"]
    assert "biometrics" in export["payload"] # Biometric allowed for SERVICE_PROVISION in Balanced

    # Verify signature
    assert core.portability.validate_import(export) is True

    # Test rejection of tampered data
    tampered = export.copy()
    tampered["payload"]["extra"] = "hack"
    assert core.portability.validate_import(tampered) is False
