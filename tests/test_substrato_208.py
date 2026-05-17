import pytest
import asyncio
from substrato_208_production_cathedral import (
    SecurityProduction,
    RegulatoryCompliance,
    ProductionLLMOps,
    ZeroDayDetector,
    AutonomousOrchestration,
    GlobalFederation,
    ArkheObservability,
    SentinelConsensusPolicy
)

class MockHSM:
    async def sign(self, data: bytes) -> str:
        return "mock_signature" * 4

@pytest.mark.asyncio
async def test_security_production():
    hsm = MockHSM()
    sec = SecurityProduction(hsm_signer=hsm)

    # Test valid FL epsilon
    val = await sec.validate_fl_epsilon(0.05, "bank_itau")
    assert val["valid"] is True

    # Test invalid FL epsilon
    val = await sec.validate_fl_epsilon(0.5, "bank_itau")
    assert val["valid"] is False

    # Test PQC sign
    sig = await sec.pqc_sign_with_fallback(b"data", "partner1")
    assert sig["method"] == "PQC"

    # Test fallback
    sec._pqc_active = False
    sig = await sec.pqc_sign_with_fallback(b"data", "partner1")
    assert sig["method"] == "ECDSA_FALLBACK"

def test_regulatory_compliance():
    comp = RegulatoryCompliance()

    # Test generation
    sub = comp.generate_submission_template("GDPR", "data_breach", 100)
    assert sub["regulation"] == "GDPR"
    assert "breach_description" in sub["required_fields"]

@pytest.mark.asyncio
async def test_regulatory_compliance_async():
    comp = RegulatoryCompliance()

    # Test DPO ticket
    ticket = await comp.create_dpo_ticket("LGPD", 8, "Data leak")
    assert ticket["severity"] == 8
    assert ticket["status"] == "OPEN"

@pytest.mark.asyncio
async def test_production_llm_ops():
    ops = ProductionLLMOps()

    reqs = [{"_id": "1", "query": "hello world"}, {"_id": "2", "query": "hello world"}]
    res = await ops.optimized_batch_inference(reqs, max_batch_size=2)

    assert len(res) == 2
    assert res[0]["cached"] is False
    assert res[1]["cached"] is True

    guard = await ops.real_time_guardrail("The capital of France is Paris", ["France is a country in Europe. Paris is its capital."])
    assert guard["blocked"] is False

@pytest.mark.asyncio
async def test_zero_day_detector():
    det = ZeroDayDetector()

    await det.ingest_misp_feed([{"id": "1", "threat_level_id": 1, "info": "malware"}])
    assert len(det._misp_feed) == 1

    res = det.train_ensemble([{}])
    assert res["ensemble_accuracy"] > 0

    alert = await det.detect_zero_day({"hash": "abc", "novelty_score": 0.9})
    assert "confidence" in alert

@pytest.mark.asyncio
async def test_autonomous_orchestration():
    orch = AutonomousOrchestration()

    orch.register_sentinel("mod1", 0.95, ["cap1"])
    orch.register_sentinel("mod2", 0.90, ["cap2"])

    res = await orch.sentinel_consensus({"action": "heal"}, SentinelConsensusPolicy.UNANIMOUS)
    assert res["consensus"] is True

    heal = await orch.auto_heal("mod3")
    assert heal["status"] == "HEALED"

    orch.set_circuit_breaker("svc1", failure_threshold=2, recovery_timeout=0.1)
    assert orch.check_circuit("svc1") is True
    orch.record_failure("svc1")
    orch.record_failure("svc1")
    assert orch.check_circuit("svc1") is False
    await asyncio.sleep(0.15)
    assert orch.check_circuit("svc1") is True

@pytest.mark.asyncio
async def test_global_federation():
    fed = GlobalFederation()

    dp = await fed.apply_cross_border_dp({"val": 10}, "BR", "RU")
    assert dp["protocol"]["effective_epsilon"] == 0.3

    sync = await fed.sync_federated_model("model1", [0.1, 0.2], "org1", "A" * 64)
    assert sync["status"] == "synced"

    fed.update_dashboard("org1", {"phi_c": 0.9})
    dash = fed.get_dashboard()
    assert dash["global_phi_c"] == 0.9

@pytest.mark.asyncio
async def test_arkhe_observability():
    obs = ArkheObservability()

    await obs.export_prometheus_metric("test_metric", 1.0, {"label": "val"})
    assert len(obs._prometheus_metrics) == 1

    trace = obs.start_trace("trace1", "op", {"phi_c": 0.9})
    obs.add_trace_span(trace, "span1", 10.0)
    assert len(trace["spans"]) == 1

    alert = await obs.check_phi_c_degradation(0.8, "svc1")
    assert alert["severity"] == "WARNING"
