import pytest
import sys
import os
import importlib.util

# Load the module dynamically to handle dashes and numbers in directory names
module_name = 'internet_mesh_2_0'
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'substrates', '200-299_expansion', 'substrato_224_internet_mesh_2_0', 'internet_mesh_2_0.py'))
spec = importlib.util.spec_from_file_location(module_name, module_path)
mesh_module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = mesh_module
spec.loader.exec_module(mesh_module)

def test_physical_layer_scan():
    node = mesh_module.InternetMesh20Node("arkhe-node-1")
    scan = node.physical.scan_spectrum()
    assert "PAN" in scan
    assert "LAN" in scan
    assert scan["PAN"] == "clear"

def test_radio_layer_profile_selection():
    node = mesh_module.InternetMesh20Node("arkhe-node-1")

    # Needs 50 Mbps at 50m -> PAN can handle it (PAN: 100m, 50Mbps)
    profile = node.radio.select_optimal_profile(50, 50, False)
    assert profile == "PAN"

    # Needs 1000 Mbps at 500m -> LAN (LAN: 1000m, 46000Mbps)
    profile = node.radio.select_optimal_profile(500, 1000, False)
    assert profile == "LAN"

    # Broadcast
    profile = node.radio.select_optimal_profile(50000, 20, True)
    assert profile == "BC"

    # Interference on LAN -> Should fallback or pick next best.
    # WAN covers it (10000m, 10000Mbps)
    node.physical.set_interference("LAN", "interference")
    profile = node.radio.select_optimal_profile(500, 1000, False)
    assert profile == "WAN"

def test_network_routing():
    node = mesh_module.InternetMesh20Node("arkhe-node-1")
    res = node.network.route_message("hello", "arkhe-node-2", "TVWS")
    assert res["status"] == "routed"
    assert res["protocol"] == "MANET IP"

def test_governance_layer():
    node = mesh_module.InternetMesh20Node("arkhe-node-1")

    assert node.governance.verify_identity("arkhe-valid") is True
    assert node.governance.verify_identity("invalid-id") is False

    assert node.governance.process_payment(5.0) is True
    assert node.governance.balance == 5.0

    assert node.governance.process_payment(10.0) is False

def test_full_transmission():
    node = mesh_module.InternetMesh20Node("arkhe-node-1")

    # Valid transmission
    res = node.transmit("arkhe-node-2", "payload data", 500, 1000, False)
    assert res.get("success") is True
    assert res["profile_used"] == "LAN"
    assert res["cost"] == 0.001

    # Invalid identity
    res2 = node.transmit("unknown-node", "payload", 50, 50, False)
    assert "error" in res2
    assert res2["error"] == "Invalid destination identity"

    # Invalid payload
    res3 = node.transmit("arkhe-node-2", "", 50, 50, False)
    assert "error" in res3
    assert res3["error"] == "Payload integrity check failed"

    # Out of money
    node.governance.balance = 0.0
    res4 = node.transmit("arkhe-node-2", "payload", 50, 50, False)
    assert "error" in res4
    assert res4["error"] == "Insufficient balance for transmission"
