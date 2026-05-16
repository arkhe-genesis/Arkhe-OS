import pytest
import asyncio
import numpy as np
from substrates.speculative.cat_phi_c import CATPhiCEngine
from substrates.speculative.societal_abm import SocietalABM

@pytest.mark.asyncio
async def test_cat_phi_c():
    engine = CATPhiCEngine()
    session = await engine.start_session("test_agent", "arkhe_architecture", items_remaining=3)
    assert session.agent_id == "test_agent"

    item = await engine.select_next_item(session)
    assert item is not None
    assert item.domain == "arkhe_architecture"

    phi_c = await engine.record_response(session, item, 0.95, True)
    assert isinstance(phi_c, float)

    report = await engine.finalize_session(session)
    assert report["items_administered"] == 1
    assert "proficiency_level" in report

@pytest.mark.asyncio
async def test_societal_abm():
    abm = SocietalABM(num_agents=50)
    assert len(abm.society.agents) == 50

    report = await abm.run_simulation(steps=10, interactions_per_step=5)
    assert report["steps"] == 10
    assert "final_phi_c" in report
    assert "final_gini" in report
