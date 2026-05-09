import pytest
import asyncio
import hashlib
from audit_logger import AuditLogger, DecisionType
from dynamic_consent_protocol import DynamicConsentProtocol, PrivacyProfile
from topological_photonics_protocol import TopologicalSovereigntyProtocol
from zk_mesh_verifier import ZKMeshVerifier

@pytest.mark.asyncio
async def test_topological_reprogramming_with_consent():
    audit = AuditLogger()
    consent = DynamicConsentProtocol(None)
    protocol = TopologicalSovereigntyProtocol(audit, consent)

    citizen_id = "citizen_42"
    mesh_id = "mesh_clements_01"
    target_unitary_hash = hashlib.sha256(b"unitary_matrix_data").hexdigest()
    phase_settings = [0.1, 0.2, 0.3]
    coupling_settings = [0.5, 0.5]

    # 1. Test without consent
    with pytest.raises(PermissionError):
        await protocol.reprogram_mesh(citizen_id, mesh_id, target_unitary_hash, phase_settings, coupling_settings)

    # 2. Grant consent and test
    consent.set_citizen_profile(citizen_id, PrivacyProfile.BALANCED, {f"reprogram_mesh_{mesh_id}": True})
    result = await protocol.reprogram_mesh(citizen_id, mesh_id, target_unitary_hash, phase_settings, coupling_settings)

    assert result["status"] == "SOVEREIGN_REPROGRAMMING_COMPLETE"
    assert "proof" in result
    assert result["decision_id"].startswith("dec_")

    # 3. Verify audit log
    records = audit.query(DecisionType.TOPOLOGICAL_CONFIG_REPROG)
    assert len(records) == 1
    assert records[0].context["mesh_id"] == mesh_id
    assert records[0].context["zk_proof"] == result["proof"]

@pytest.mark.asyncio
async def test_disorder_benchmarking():
    audit = AuditLogger()
    consent = DynamicConsentProtocol(None)
    protocol = TopologicalSovereigntyProtocol(audit, consent)

    mesh_id = "mesh_clements_01"
    disorder_params = {"sigma": 0.05, "type": "gaussian_phase_noise"}
    system_response = {"fidelity": 0.98, "topological_invariant_preserved": True}

    entry_hash = await protocol.register_disorder_benchmark(mesh_id, disorder_params, system_response)

    assert len(entry_hash) == 64 # SHA-256
    status = protocol.get_ledger_status()
    assert status["disorder_benchmark_count"] == 1
    assert status["last_benchmark_hash"] == entry_hash

    # Verify audit
    records = audit.query(DecisionType.DISORDER_BENCHMARK)
    assert len(records) == 1
    assert records[0].context["entry_hash"] == entry_hash

@pytest.mark.asyncio
async def test_zk_integrity_verification():
    audit = AuditLogger()
    consent = DynamicConsentProtocol(None)
    protocol = TopologicalSovereigntyProtocol(audit, consent)

    target_unitary_hash = "hash_abc_123"
    fake_proof = "proof_valid_hash"

    is_valid = await protocol.verify_mesh_integrity(fake_proof, target_unitary_hash)
    assert is_valid is True

    invalid_proof = "invalid_format"
    is_not_valid = await protocol.verify_mesh_integrity(invalid_proof, target_unitary_hash)
    assert is_not_valid is False

    # Verify audit
    records = audit.query(DecisionType.ZK_MESH_VERIFICATION)
    assert len(records) == 2
    assert records[0].context["is_valid"] is False
    assert records[1].context["is_valid"] is True
