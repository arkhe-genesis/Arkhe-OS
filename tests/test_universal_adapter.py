import pytest
import asyncio
import time
import importlib.util

# Dynamically import because of the number in the package name
spec = importlib.util.spec_from_file_location("universal_adapter", "substrates/9007_polyglot_mesh/universal_adapter.py")
universal_adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(universal_adapter)
UniversalAdapter = universal_adapter.UniversalAdapter
ArkheRequestContext = universal_adapter.ArkheRequestContext

class MockTemporalChain:
    def __init__(self):
        self.anchored_events = []

    async def anchor_event(self, event_type, metadata):
        self.anchored_events.append((event_type, metadata))
        return "anchor_id_123"

class MockPhiMonitor:
    @property
    def current_coherence(self):
        return 0.999

@pytest.mark.asyncio
async def test_universal_adapter_process_request():
    temporal = MockTemporalChain()
    phi = MockPhiMonitor()
    adapter = UniversalAdapter(temporal, phi)

    headers = {"X-Arkhe-ORCID": "user_123"}
    body = {"data": "test"}

    result = await adapter.process_request("POST", "/api/test", headers, body)

    assert "context" in result
    assert "anchor" in result
    assert result["anchor"] == "anchor_id_123"

    ctx = result["context"]
    assert isinstance(ctx, ArkheRequestContext)
    assert ctx.orcid == "user_123"
    assert ctx.phi_c == 0.999
    assert len(ctx.trace_id) <= 16

    assert len(temporal.anchored_events) == 1
    event_type, metadata = temporal.anchored_events[0]
    assert event_type == "api_request"
    assert metadata["orcid"] == "user_123"
    assert metadata["path"] == "/api/test"
    assert metadata["method"] == "POST"

@pytest.mark.asyncio
async def test_universal_adapter_process_response():
    temporal = MockTemporalChain()
    phi = MockPhiMonitor()
    adapter = UniversalAdapter(temporal, phi)

    ctx = ArkheRequestContext(orcid="user_123", phi_c=0.999, trace_id="trace_123")

    await adapter.process_response(ctx, 200, {"status": "ok"})

    assert len(temporal.anchored_events) == 1
    event_type, metadata = temporal.anchored_events[0]
    assert event_type == "api_response"
    assert metadata["status"] == 200
    assert metadata["trace_id"] == "trace_123"
