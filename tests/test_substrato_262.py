import pytest
import asyncio
from substrato_262 import ArkheResearchSynthesisEngine, ArkheResearchBusInterface, CanonicalResearchPlan

@pytest.mark.asyncio
async def test_engine():
    engine = ArkheResearchSynthesisEngine("Test research text")
    plan = await engine.canonize()

    assert plan.total_phases == 23
    assert plan.total_tiers == 3
    assert plan.total_properties == 5
    assert plan.total_macros == 3
    assert plan.total_workflow_steps == 8
    assert plan.total_axioms == 42

    assert plan.phi_c_completeness == 1.0

    bus = ArkheResearchBusInterface(engine)
    success, seal = await bus.publish_to_bus(plan)
    assert success is True
