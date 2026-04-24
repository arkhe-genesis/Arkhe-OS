import pytest
import time
from catedrald_cloud_security import CloudSecuritySubstrate, inject_cloud_security_into_core

class MockCore:
    def __init__(self):
        self.coherence = 1.0
        self.evo = type('obj', (object,), {'population': []})
    def inject_coherence(self, delta):
        self.coherence = min(1.0, self.coherence + delta)
    def get_coherence(self):
        return self.coherence

def test_cloud_security_initialization():
    core = MockCore()
    cloud_sec = inject_cloud_security_into_core(core)
    assert cloud_sec.name == "CrystalFortress_Alpha"
    assert cloud_sec.zero_trust_enabled is True
    assert len(cloud_sec.regions) == 3

def test_cloud_security_deploy():
    cs = CloudSecuritySubstrate()
    result = cs.deploy_fortress()
    assert result["status"] == "deployed"
    assert result["zero_trust"] == "enforced"

def test_cloud_security_integrity():
    cs = CloudSecuritySubstrate()
    assert cs.verify_integrity() is True

    # Simulate region failure
    cs.regions[0].status = "failed"
    cs.regions[1].status = "failed"
    assert cs.verify_integrity() is False
    assert cs.quórum_status == "compromised"

def test_cloud_security_get_status():
    cs = CloudSecuritySubstrate()
    status = cs.get_status()
    assert status["substrate_id"] == 67
    assert "sovereignty_score" in status
    assert len(status["regions"]) == 3
