import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from darkweb_monitor.tor_shield import TorVigilShield, DarknetProtocol

class MockToolSystem:
    async def invoke_tool(self, name, args):
        return True

class MockDeltaMem:
    pass

class MockHSM:
    async def sign(self, payload: bytes, key_label: str) -> str:
        return "mock_pqc_signature"

class MockTemporal:
    async def anchor_event(self, event_type, payload):
        return "mock_temporal_seal"

@pytest.mark.asyncio
async def test_tor_shield():
    tools = MockToolSystem()
    delta = MockDeltaMem()
    hsm = MockHSM()
    temporal = MockTemporal()

    perceptual_db = {
        "hash1234567890abcdef": {
            "confidence": 0.99,
            "type": "csam",
            "source": "darknet_example"
        }
    }

    shield = TorVigilShield(tools, delta, hsm, temporal, perceptual_db)

    findings = await shield.monitor_onion_service("http://exampleonion.onion")

    assert len(findings) == 1
    assert findings[0].violation_type == "csam"
    assert findings[0].protocol == DarknetProtocol.TOR
    assert findings[0].onion_address == "http://exampleonion.onion"
    assert findings[0].perceptual_hash_match == "hash1234567890abcdef"
    assert findings[0].temporal_seal == "mock_temporal_seal"

    await shield.report_to_authorities(findings)
    assert "Interpol" in findings[0].reported_to
