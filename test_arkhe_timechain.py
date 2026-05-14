import asyncio
import pytest
from arkhe_timechain.core import TemporalChain, EventType, CausalLink
from arkhe_timechain.ma_s2_integration import MA_S2_TimechainIntegration
import os

@pytest.fixture
async def temp_chain():
    db_path = "test_timechain_pytest.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    tc = TemporalChain(storage_backend="sqlite", storage_config={"path": db_path})
    yield tc
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.mark.asyncio
async def test_anchor_event(temp_chain):
    tc = temp_chain
    anchor = await tc.anchor_event(
        event_type=EventType.CUSTOM,
        payload={"test": "data"},
        metadata={"user": "test_user"}
    )
    assert anchor.position == 0
    assert anchor.event.payload["test"] == "data"
    assert tc.event_count == 1

@pytest.mark.asyncio
async def test_causal_deps(temp_chain):
    tc = temp_chain
    anchor1 = await tc.anchor_event(
        event_type=EventType.CUSTOM,
        payload={"step": 1}
    )
    anchor2 = await tc.anchor_event(
        event_type=EventType.CUSTOM,
        payload={"step": 2},
        causal_deps=[anchor1.event.event_id]
    )
    assert len(anchor2.event.causal_deps) == 1
    assert anchor2.event.causal_deps[0].event_id == anchor1.event.event_id
    assert tc.event_count == 2
    assert await tc.verify_chain() == True

@pytest.mark.asyncio
async def test_mas2_integration(temp_chain):
    tc = temp_chain
    mas2 = MA_S2_TimechainIntegration(tc)
    seal = await mas2.log_control_execution(
        control_id="CVS-0.1",
        execution_result={"status": "compliant"}
    )
    proof = await mas2.generate_compliance_proof(["CVS-0.1"])
    assert proof["event_count"] == 1
    assert len(proof["event_seals"]) == 1
    assert seal.startswith(proof["event_seals"][0].strip("."))
