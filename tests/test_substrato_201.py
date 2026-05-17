import pytest
import asyncio
from sovereignty.digital_sovereignty_core import DigitalSovereigntyFramework, SovereigntyPrinciple

class MockTemporalChain:
    def __init__(self):
        self.events = []

    async def anchor_event(self, event_type, data):
        seal = f"mock_seal_{len(self.events)}"
        self.events.append({
            "type": event_type,
            "data": data,
            "seal": seal
        })
        return seal

@pytest.mark.asyncio
async def test_digital_sovereignty_framework():
    temporal_chain = MockTemporalChain()
    framework = DigitalSovereigntyFramework(temporal_chain=temporal_chain)

    report = await framework.audit_sovereignty()

    assert "audit_id" in report
    assert "sovereignty_phi_c" in report
    assert report["sovereignty_phi_c"] > 0
    assert "details" in report

    assert len(report["details"]) == 10

    for principle in SovereigntyPrinciple:
        assert principle.value in report["details"]
        detail = report["details"][principle.value]
        assert "compliance_score" in detail
        assert "evidence" in detail
        assert "temporal_seal" in detail

    assert len(temporal_chain.events) == 11 # 10 principles + 1 report

    assert temporal_chain.events[-1]["type"] == "sovereignty_framework_audit"
