import sys
import os

# Ensure the substrate path is available for import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'substrates', '300-399_foundations', 'substrato_361')))

import pytest
from substrato_361_hypercycle import ArkheHyperCycleNode, ArkheHyperCycleNodeFixed, HyperCycleNetwork

def test_hypercycle_node_initialization():
    node = ArkheHyperCycleNode(node_id="HNN-TEST-01")
    status = node.get_node_status()
    assert status["node_id"] == "HNN-TEST-01"
    assert status["node_type"] == "HNN"
    assert status["status"] == "initialized"

def test_hypercycle_node_fixed_humility():
    node = ArkheHyperCycleNodeFixed(node_id="HNN-TEST-02")
    task_complex = {"id": "t1", "complexity": 0.8}
    humility_complex = node._compute_humility(task_complex)
    assert humility_complex > node.ghost

    task_simple = {"id": "t2", "complexity": 0.1}
    humility_simple = node._compute_humility(task_simple)
    assert humility_simple < node.ghost

def test_hypercycle_network():
    network = HyperCycleNetwork(n_nodes=10)
    assert len(network.nodes) == 10 + 5 # 10 HNN + 5 HBN
    stats = network.get_network_statistics()
    assert stats["total_nodes"] == 15
