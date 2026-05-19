import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from integration_optical_bus.token_arkhe_optical_bus import TokenArkheOpticalBus

@pytest.fixture
def optical_bus():
    return TokenArkheOpticalBus(num_nodes=16)

def test_optical_bus_initialization(optical_bus):
    assert optical_bus.simulator.num_nodes == 16
    assert optical_bus.simulator.entanglement_matrix is not None

def test_submit_payload_android(optical_bus):
    result = optical_bus.submit_payload("agent_android_01", "android", "compliance_check_data")

    assert result["agent_id"] == "agent_android_01"
    assert result["platform"] == "android"
    assert isinstance(result["is_compliant"], bool)
    assert isinstance(result["global_phi_c"], float)
    assert result["global_phi_c"] < 1.0
    assert result["consensus_seal"].startswith("optical_consensus_")
    assert result["verification_type"] == "quantum_polaritonic_collective"

def test_submit_payload_ios(optical_bus):
    result = optical_bus.submit_payload("agent_ios_02", "ios", "crypto_validation_payload")

    assert result["agent_id"] == "agent_ios_02"
    assert result["platform"] == "ios"
    assert isinstance(result["is_compliant"], bool)
    assert isinstance(result["global_phi_c"], float)
    assert result["global_phi_c"] < 1.0
    assert result["consensus_seal"].startswith("optical_consensus_")

def test_submit_payload_azure(optical_bus):
    result = optical_bus.submit_payload("agent_azure_03", "azure", "cloud_sync_data")

    assert result["agent_id"] == "agent_azure_03"
    assert result["platform"] == "azure"
    assert isinstance(result["is_compliant"], bool)
    assert isinstance(result["global_phi_c"], float)
    assert result["global_phi_c"] < 1.0
    assert result["consensus_seal"].startswith("optical_consensus_")
