import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from network.network_complex_hit_136 import NetworkComplex, Node, Link, Face, CleanExitValidator

class TestNetworkComplexHit136:

    def test_betti_1_2_1_is_torus(self):
        # A HIT with Betti 1-2-1 should have faces representing the 2-cells
        network = NetworkComplex()
        network.add_node(Node("A", "Interior"))
        network.add_node(Node("B", "Interior"))
        network.add_node(Node("C", "Interior"))

        network.add_link(Link("A", "B", 1.0))
        network.add_link(Link("B", "C", 1.0))
        network.add_link(Link("C", "A", 1.0))

        # Add 2-cell (Face) to make Betti 2 >= 1
        network.add_face(Face("A", "B", "C", True))

        assert len(network.nodes) == 3
        assert len(network.links) == 3
        assert len(network.faces) == 1

    def test_is_contr_by_zone(self):
        network = NetworkComplex()

        # Interior zone
        network.add_node(Node("A", "Interior"))
        network.add_node(Node("B", "Interior"))
        network.add_link(Link("A", "B", 1.0)) # Latency < 3.0s

        # Saturn zone
        network.add_node(Node("C", "Saturn"))
        network.add_node(Node("D", "Saturn"))
        network.add_link(Link("C", "D", 20000.0)) # Latency > timeout

        validator = CleanExitValidator(network)

        # Interior should be isContr
        assert validator.is_contr("Interior") == True

        # Saturn should NOT be isContr (it's eventually connected)
        assert validator.is_contr("Saturn") == False

if __name__ == "__main__":
    pytest.main([__file__])
