import pytest
import asyncio
import json
import time
from src.cathedral.intent.intent_kernel import IntentKernel, ArkheIntentKernel, IntentPacket
from cathedral_codex import CrystalCodex

class MockCoherenceField:
    async def get_current_coherence(self, origin: str) -> float:
        if origin == "high_omega":
            return 0.99
        return 0.50

@pytest.fixture
def codex():
    return CrystalCodex()

@pytest.fixture
def kernel(codex):
    return IntentKernel(codex=codex, coherence_field=MockCoherenceField())

@pytest.fixture
def arkhe_kernel(codex):
    return ArkheIntentKernel(codex=codex, coherence_field=MockCoherenceField())

@pytest.mark.asyncio
async def test_lexical_validation_failure(kernel):
    packet = IntentPacket(
        intent_id="i1",
        origin="high_omega",
        action_graph={},
        context={},
        signature="invalid-sig"
    )
    result = await kernel.execute_intent(packet)
    assert result["status"] == "error"
    assert "lexical_error" in result["reason"]

@pytest.mark.asyncio
async def test_semantic_validation_failure(kernel):
    packet = IntentPacket(
        intent_id="i1",
        origin="high_omega",
        action_graph={"@type": "ReserveAction", "target": {}}, # Missing fields
        context={},
        signature="ecdsa-valid"
    )
    result = await kernel.execute_intent(packet)
    assert result["status"] == "error"
    assert "semantic_ambiguity" in result["reason"]

@pytest.mark.asyncio
async def test_pragmatic_validation_failure(kernel):
    packet = IntentPacket(
        intent_id="i1",
        origin="low_omega",
        action_graph={
            "@type": "QueryAction",
            "target": {"query": "test"}
        },
        context={"coherence_threshold": 0.90},
        signature="ecdsa-valid"
    )
    result = await kernel.execute_intent(packet)
    assert result["status"] == "error"
    assert "insufficient_coherence" in result["reason"]

@pytest.mark.asyncio
async def test_causal_validation_failure(kernel):
    packet = IntentPacket(
        intent_id="i1",
        origin="high_omega",
        action_graph={
            "@type": "QueryAction",
            "target": {"query": "test"}
        },
        context={"validity_ns": int(time.time() * 1e9) - 1000}, # Expired
        signature="ecdsa-valid"
    )
    result = await kernel.execute_intent(packet)
    assert result["status"] == "error"
    assert "causal_inconsistency" in result["reason"]

@pytest.mark.asyncio
async def test_successful_execution_jsonld(arkhe_kernel, codex):
    intent_json = json.dumps({
        "id": "intent_001",
        "issuer": {"did": "high_omega"},
        "action": {
            "@type": "ReserveAction",
            "target": {
                "identifier": "FLIGHT-123",
                "departureDate": "2026-12-12"
            },
            "parameters": {
                "passengers": 2
            }
        }
    })

    result = await arkhe_kernel.process_intent_json(intent_json)
    assert result["status"] == "success"
    assert result["intent_id"] == "intent_001"
    assert "causal_hash" in result

    # Verify anchoring
    artifact = await codex.get_artifact("intent_execution_intent_001")
    assert artifact is not None
    assert artifact["hash"] == result["causal_hash"]

@pytest.mark.asyncio
async def test_successful_execution_fs190_graph(kernel, codex):
    packet = IntentPacket(
        intent_id="intent_002",
        origin="high_omega",
        action_graph={
            "nodes": [
                {"id": "n1", "type": "action", "verb": "transfer_ownership", "params": {"to": "wallet_x"}}
            ]
        },
        context={},
        signature="ecdsa-valid"
    )

    result = await kernel.execute_intent(packet)
    assert result["status"] == "success"
    assert result["data"]["action"] == "ownership_transferred"
    assert result["data"]["to"] == "wallet_x"

    # Verify anchoring
    artifact = await codex.get_artifact("intent_execution_intent_002")
    assert artifact is not None
