import pytest
import asyncio
from arkhe_retrocausal.ping_kernel import RetrocausalPingKernel
from arkhe_retrocausal.retrocausal_dream import RetrocausalDreamEngine, RetrocausalDreamScheduler
from arkhe_retrocausal.sovereign_gap_calculator import SovereignGapCalculator

def test_ping_kernel_full_cycle():
    kernel = RetrocausalPingKernel()
    intention_seal = "test_seal"
    payload = {"data": "test"}
    phi_c_current = 0.8
    advanced_response = "ack"
    phi_c_future = 0.9

    result = kernel.full_retrocausal_cycle(
        intention_seal, payload, phi_c_current, advanced_response, phi_c_future
    )

    assert "novelty_generated" in result
    assert result["novelty_generated"] > 0
    assert result["collapse"]["is_novelty_generated"] is True

def test_sovereign_gap_calculator():
    gap = SovereignGapCalculator.compute_gap(0.8, 0.9)
    assert abs(gap - 0.1) < 0.001

    assert SovereignGapCalculator.is_in_optimal_range(0.8) is True
    assert SovereignGapCalculator.is_in_optimal_range(0.1) is False

@pytest.mark.asyncio
async def test_retrocausal_dream():
    class DummyAdapter:
        def __init__(self):
            self.agent_id = "test_agent"

    adapter = DummyAdapter()
    scheduler = RetrocausalDreamScheduler(adapter)

    scheduler.record_day_event({"description": "event 1"})
    scheduler.record_day_event({"description": "event 2"})

    seal, new_phi_c = await scheduler.night_cycle()

    assert seal is not None
    assert new_phi_c != 0.85 # Should be modified
