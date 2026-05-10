import pytest
import numpy as np

from metabolic_router import MetabolicTemporalRouter

class MockEdge:
    def __init__(self, src, dst, score=1.0):
        self.src = src
        self.dst = dst
        self.score = score

class MockRoutingTable:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def node_index(self, node):
        return self.nodes.index(node)

class MockOracle:
    def evaluate_causal_edge(self, edge):
        return edge.score

def test_metabolic_router_integration():
    # A -> B -> C
    # B -> D
    nodes = ['A', 'B', 'C', 'D']
    edges = [
        MockEdge('A', 'B', 1.0),
        MockEdge('B', 'C', 1.0),
        MockEdge('B', 'D', 0.5) # Fails oracle
    ]
    rt = MockRoutingTable(nodes, edges)
    router = MetabolicTemporalRouter(rt)
    oracle = MockOracle()

    fluxes = router.maximize_delivery('A', 'C', oracle)

    assert fluxes[0] > 0
    assert fluxes[1] > 0
    assert fluxes[2] == 0
