import pytest
from arkhe_os.federation_protocol.cross_platform_federation import FederationProtocol, Node, WormholeConfig

def test_discovery():
    protocol = FederationProtocol()
    peer = Node("peer_001", "226192a177a8b3bc")
    config = WormholeConfig(2, 5.0, 1.0, 2)
    result = protocol.discover(peer, config)
    assert result["status"] == "ACCEPTED"
    assert result["seal_match"] is True

def test_discovery_invalid():
    protocol = FederationProtocol()
    peer = Node("peer_001", "bc9d6704dd4aa153")
    config = WormholeConfig(1, 2.0, 1.0, 1) # Invalid compared to canonical
    result = protocol.discover(peer, config)
    assert result["status"] == "REJECTED"
    assert "not physically valid" in result["reason"]

def test_geometric_handshake():
    protocol = FederationProtocol()
    peer = Node("peer_001", "226192a177a8b3bc")
    result = protocol.handshake(peer)
    assert result["status"] == "ESTABLISHED"
    assert result["throat_length"] == protocol.canonical_wormhole.throat_length

def test_federated_transmission():
    protocol = FederationProtocol()
    sender = Node("node_alpha", "226192a177a8b3bc")
    recipient = Node("node_beta", "226192a177a8b3bc")
    result = protocol.transmit(sender, recipient, "payload", 0.1204864390215327)
    assert result["status"] == "ACCEPTED"
    assert result["casimir_perturbation"] == 0.1204864390215327

def test_cross_attestation():
    protocol = FederationProtocol()
    result = protocol.attest("hash", "226192a177a8b3bc")
    assert result["status"] == "ATTESTED"

def test_rejection_invalid_perturbation():
    protocol = FederationProtocol()
    sender = Node("node_alpha", "226192a177a8b3bc")
    recipient = Node("node_beta", "226192a177a8b3bc")
    result = protocol.transmit(sender, recipient, "payload", 1.0) # > 0.7015
    assert result["status"] == "REJECTED"
    assert "exceeds energy gap" in result["reason"]
