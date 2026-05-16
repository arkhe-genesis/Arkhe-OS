import pytest
import asyncio
from substrato_217_recon_canon_operational import ReconCanonOperationalization

@pytest.mark.asyncio
async def test_substrato_217_execution():
    orchestrator = ReconCanonOperationalization()
    result = await orchestrator.run_all("arkhe.network")

    assert result["substrate"] == 217
    assert result["status"] == "ALL_TESTS_PASSED"
    assert result["global_phi_c_coherence"] >= 0.90

    # E2E Field
    e2e = result["field_e2e_validation"]
    assert e2e["status"] == "PASS"
    assert e2e["end_to_end_latency_ms"] < 300

    # HSM
    hsm = result["hsm_certification"]
    assert hsm["status"] == "READY_FOR_SUBMISSION"
    assert hsm["key_export_prevention"] == "100%"
    assert hsm["signing_time_ms"] <= 150

    # Multimodal
    mm = result["multimodal_training"]
    assert mm["status"] == "TRAINED"
    assert mm["prediction_accuracy_top1"] >= 0.80

    # DP Federation
    dp = result["adaptive_dp_federation"]
    assert dp["status"] == "ACTIVE"
    assert dp["jurisdiction_compliance"] == "100%"

    # Recon
    recon = result["recon_playbook"]
    assert recon["status"] == "COMPLETED"
    assert recon["aggregated_phi_c"] >= 0.90
