import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from runtime.wormhole.engine import TraversableWormholeEngine
from agi.system32.federation.substrate_330 import FederationProtocol

class TestSubstrate330(unittest.TestCase):
    def setUp(self):
        self.node_a = FederationProtocol("node_A", TraversableWormholeEngine)
        self.node_b = FederationProtocol("node_B", TraversableWormholeEngine)
        self.canonical_config = {'q': 2, 'g': 5.0, 'Nf': 2}

    def test_discovery(self):
        res = self.node_a.discover_node("node_B")
        self.assertEqual(res["status"], "discovered")

    def test_handshake(self):
        # A initiates handshake with B
        success_a = self.node_a.geometric_handshake("node_B", self.canonical_config)
        self.assertTrue(success_a)

        # B initiates handshake with A
        success_b = self.node_b.geometric_handshake("node_A", self.canonical_config)
        self.assertTrue(success_b)

        # Seals should match
        seal_a = self.node_a.channels["node_B"]["seal"]
        seal_b = self.node_b.channels["node_A"]["seal"]
        self.assertEqual(seal_a, seal_b)

    def test_transmission_and_attestation(self):
        self.node_a.geometric_handshake("node_B", self.canonical_config)
        self.node_b.geometric_handshake("node_A", self.canonical_config)

        message = self.node_a.transmit("node_B", "INITIATE_FEDERATION_SYNC")
        self.assertIsNotNone(message)

        is_valid = self.node_b.attest_message(message)
        self.assertTrue(is_valid)

if __name__ == '__main__':
    unittest.main()
