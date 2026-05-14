import pytest
from arkp_asi.src.asi_node_registry import ASINodeRegistry, ASINodeMetadata, NodeCapability
from arkhe.network.asi_connection_protocol import ASIConnectionProtocol, ASIConnectionState

class ConsistencyOracle:
    def __init__(self, node_id=None):
        self.node_id = node_id
    def anchor_event(self, event_type, payload, causal_deps):
        return "mock_anchor"

def test_registry():
    oracle = ConsistencyOracle()
    registry = ASINodeRegistry(oracle)
    assert len(registry.known_nodes) == 0

def test_protocol_import():
    assert ASIConnectionProtocol is not None
    assert ASIConnectionState.CONNECTED.value == "connected"
