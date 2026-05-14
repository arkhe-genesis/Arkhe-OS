import pytest
import asyncio
import time
from arkhe_timechain.core import TemporalChain, EventType

@pytest.mark.asyncio
async def test_timechain_initialization():
    chain = TemporalChain(storage_backend="in_memory")
    assert chain.event_count == 0
    assert chain.current_seal == "0" * 64
    assert chain.merkle_root is None

@pytest.mark.asyncio
async def test_timechain_anchor_event():
    chain = TemporalChain(storage_backend="in_memory")
    payload = {"user": "test_user", "action": "login"}

    anchor = await chain.anchor_event(
        event_type=EventType.CUSTOM,
        payload=payload,
    )

    assert anchor is not None
    assert chain.event_count == 1
    assert chain.current_seal == anchor.chain_seal
    assert anchor.event.payload == payload

@pytest.mark.asyncio
async def test_timechain_query_and_verify():
    chain = TemporalChain(storage_backend="in_memory")

    await chain.anchor_event(
        event_type=EventType.CVS_SCAN,
        payload={"scan": "started"},
    )
    await chain.anchor_event(
        event_type=EventType.APM_PATH,
        payload={"path": "/app/secure"},
    )

    assert chain.event_count == 2

    events = await chain.query_events(event_type=EventType.CVS_SCAN)
    assert len(events) == 1
    assert events[0].event_type == EventType.CVS_SCAN

    is_valid = await chain.verify_chain()
    assert is_valid is True
