import pytest
import asyncio
from rights_shield.content_guardian import ImageRightsGuardian, ViolationType

class TemporalChainMock:
    async def anchor_event(self, event_type: str, data: dict) -> str:
        return "mock_temporal_seal"

class HSMMock:
    async def sign(self, data: bytes, key_label: str = "default") -> dict:
        return {"signature_hex": "mock_pqc_signature"}

class DeltaMemMock:
    async def predict_zero_day(self, features: dict) -> dict:
        return {"is_zero_day": True, "confidence": 0.95}

class ToolSystemMock:
    def __init__(self):
        self.invocations = []

    async def invoke_tool(self, name: str, params: dict):
        self.invocations.append({"name": name, "params": params})

class PentestRegistryMock:
    pass

@pytest.fixture
def guardian():
    tool_system = ToolSystemMock()
    delta_mem = DeltaMemMock()
    hsm = HSMMock()
    temporal = TemporalChainMock()
    pentest_registry = PentestRegistryMock()
    return ImageRightsGuardian(tool_system, delta_mem, hsm, temporal, pentest_registry)

@pytest.mark.asyncio
async def test_register_authorized_content(guardian):
    image_bytes = b"test_image_data"
    creator_id = "test_creator"

    fp = await guardian.register_authorized_content(image_bytes, creator_id)

    assert fp is not None
    assert fp.perceptual_hash is not None
    assert fp.pqc_signature == "mock_pqc_signature"
    assert fp.temporal_seal == "mock_temporal_seal"

    # Assert that the content is registered in the guardian's dictionary
    assert fp.perceptual_hash in guardian._authorized_fingerprints

@pytest.mark.asyncio
async def test_scan_for_violations_unauthorized(guardian):
    image_bytes = b"fake_image_data" # Matches mock extractor output
    creator_id = "test_creator"
    await guardian.register_authorized_content(image_bytes, creator_id)

    findings = await guardian.scan_for_violations(["http://test.com/img.jpg"])

    assert len(findings) == 1
    assert findings[0]["violation"] == ViolationType.UNAUTHORIZED_DISTRIBUTION

@pytest.mark.asyncio
async def test_scan_for_violations_deepfake(guardian):
    # Don't register the image so it's treated as unknown and checked for deepfake
    findings = await guardian.scan_for_violations(["http://test.com/deepfake.jpg"])

    assert len(findings) == 1
    assert findings[0]["violation"] == ViolationType.DEEPFAKE_EXPLICIT

@pytest.mark.asyncio
async def test_orchestrate_takedown(guardian):
    image_bytes = b"fake_image_data"
    creator_id = "test_creator"
    await guardian.register_authorized_content(image_bytes, creator_id)

    findings = [{"url": "http://test.com/img.jpg", "violation": ViolationType.UNAUTHORIZED_DISTRIBUTION, "hash": guardian._authorized_fingerprints.copy().popitem()[0]}]

    res = await guardian.orchestrate_takedown(findings)

    assert res["actions_taken"] == 1
    assert len(guardian.tools.invocations) == 1

    invocation = guardian.tools.invocations[0]
    assert invocation["name"] == "api_external_call"
    assert invocation["params"]["method"] == "POST"
    assert "notice_type" in invocation["params"]["payload"]

@pytest.mark.asyncio
async def test_judicial_automation_missing_hash():
    from rights_shield.judicial_automation import JudicialAutomationModule
    hsm = HSMMock()
    temporal = TemporalChainMock()
    automation = JudicialAutomationModule(hsm, temporal)

    violation = {
        "url": "http://test.com/missing-hash.jpg"
        # hash key omitted deliberately
    }

    # Should not raise KeyError
    filing = await automation.file_automated_petition(
        violation=violation,
        jurisdiction="BR",
        relief_sought=["takedown"],
        plaintiff_consent=True
    )

    assert filing.defendant_url == "http://test.com/missing-hash.jpg"
    assert filing.system.name == "PJE_BR"
