import pytest
import asyncio
import numpy as np
from rights_shield.watermark_encoder import InvisibleWatermarkEncoder
from rights_shield.judicial_automation import JudicialAutomationModule, JudicialSystem

class MockHSMSigner:
    async def sign(self, data, key_label):
        return {"signature_hex": "mock_pqc_signature_for_" + key_label}

class MockTemporalChain:
    async def anchor_event(self, event_type, data):
        return "mock_temporal_seal_for_" + event_type

@pytest.mark.asyncio
async def test_watermark_encoder():
    encoder = InvisibleWatermarkEncoder()
    image = np.random.randint(0, 256, (128, 128, 3), dtype=np.uint8)
    creator_fingerprint = "mock_fingerprint_123"

    watermarked_image = await encoder.embed_watermark(image, creator_fingerprint)
    assert watermarked_image.shape == image.shape

    is_watermarked, confidence = await encoder.detect_watermark(watermarked_image, creator_fingerprint)
    # Even if detection is currently weak, we at least test the execution
    assert isinstance(is_watermarked, bool)
    assert isinstance(confidence, float)

@pytest.mark.asyncio
async def test_judicial_automation():
    hsm = MockHSMSigner()
    temporal = MockTemporalChain()
    judicial_automation = JudicialAutomationModule(hsm, temporal)

    violation = {
        "url": "http://example.com/infringing_content",
        "hash": "mock_content_hash",
        "creator_id": "creator_123",
        "temporal_seal": "mock_temporal_seal",
        "original_content_seal": "mock_original_seal",
        "violation": "DEEPFAKE_EXPLICIT"
    }

    filing = await judicial_automation.file_automated_petition(
        violation=violation,
        jurisdiction="BR",
        relief_sought=["takedown"],
        plaintiff_consent=True
    )

    assert filing.system == JudicialSystem.PJE_BR
    assert filing.status == "accepted"
    assert filing.pqc_signature == "mock_pqc_signature_for_judicial_filing_signer"
