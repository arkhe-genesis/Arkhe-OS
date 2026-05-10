import pytest
from cathedral_neuro.src.cathedral_neuro.consent.consent import NeuralConsentManager

@pytest.mark.asyncio
async def test_consent_flow():
    manager = NeuralConsentManager()
    did = "did:cathedral:scientist:test"
    await manager.update_consent(did, "M1", "robotic_control", True)

    assert await manager.check(did, "M1", "robotic_control") is True
    assert await manager.check(did, "M1", "other") is False

    await manager.revoke_all(did)
    assert await manager.check(did, "M1", "robotic_control") is False
