import pytest
import numpy as np
from orquestrador.evolutionary_loop import EvolutionaryLoop
from privacy.differential_privacy_validator import DifferentialPrivacyEngine, DPReport

@pytest.mark.asyncio
async def test_evolutionary_loop_aggregation():
    # Mock classes
    class MockConsensus:
        async def propose_model_update(self, update, min_phi_c):
            return True
        async def adjust_weights(self, adjustments):
            pass

    class MockPhiBus:
        async def get_coherence_window(self, minutes):
            return {
                "node_1": {"avg_phi_c": 0.9999, "weight": 0.5, "local_gradients": [0.1, 0.2, 0.3]},
                "node_2": {"avg_phi_c": 0.97, "weight": 0.5, "local_gradients": [0.2, 0.3, 0.4]}
            }
        async def broadcast(self, topic, payload):
            pass

    class MockTemporal:
        async def anchor_event(self, event_type, payload):
            pass

    loop = EvolutionaryLoop(MockConsensus(), MockPhiBus(), MockTemporal(), DifferentialPrivacyEngine())
    metrics = await loop.phi_bus.get_coherence_window(minutes=60)
    agg = await loop._federated_aggregation(metrics)
    assert len(agg["gradients"]) == 3

    adjustments = loop._compute_weight_adjustments(metrics)
    assert "node_1" in adjustments
    assert "node_2" in adjustments
    assert adjustments["node_1"] > 0
    assert adjustments["node_2"] < 0

def test_differential_privacy_validator():
    engine = DifferentialPrivacyEngine(default_epsilon=1.0)
    model_update = {
        "version": 1,
        "gradients": [1.0, 2.0, 3.0]
    }
    safe_update = engine.apply_dp(model_update, epsilon=1.0, delta=1e-5)
    assert "privacy_params" in safe_update
    assert safe_update["privacy_params"]["epsilon"] == 1.0

    report = engine.validate_privacy(["sample1", "sample2"], safe_update)
    assert not report.privacy_violation
    assert report.proof_hash is not None

    safe_update_invalid = safe_update.copy()
    safe_update_invalid["privacy_params"]["epsilon"] = 2.0
    report_invalid = engine.validate_privacy(["sample1"], safe_update_invalid)
    assert report_invalid.privacy_violation
