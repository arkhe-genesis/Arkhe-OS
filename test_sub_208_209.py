import torch
import torch.nn as nn
import unittest
from arkhe_os.crypto.hypergraph_fhe import HypergraphFHE
from arkhe_os.ai.fhe_federated_aggregation import FHEFederatedAggregator
from arkhe_os.core.meta_abstraction_protocol import MetaAbstractionProtocol, MetaAbstractionLevel

class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(2, 2, bias=False)
        # Initialize with known weights
        with torch.no_grad():
            self.fc.weight.copy_(torch.tensor([[1.0, 2.0], [3.0, 4.0]]))

class TestSubstrates208And209(unittest.TestCase):
    def test_fhe_federated_aggregator(self):
        # 1. Setup global model and FHE module
        global_model = SimpleModel()
        fhe = HypergraphFHE(key_size=10, noise_level=0.0) # Set noise to 0 for deterministic testing
        aggregator = FHEFederatedAggregator(global_model, fhe)

        # 2. Simulate user updates
        # User 1 update: [[2.0, 4.0], [6.0, 8.0]]
        update_1 = {"fc.weight": torch.tensor([[2.0, 4.0], [6.0, 8.0]])}

        # User 2 update: [[0.0, 0.0], [0.0, 0.0]]
        update_2 = {"fc.weight": torch.tensor([[0.0, 0.0], [0.0, 0.0]])}

        # Encrypt updates
        enc_update_1 = {k: fhe.encrypt(v) for k, v in update_1.items()}
        enc_update_2 = {k: fhe.encrypt(v) for k, v in update_2.items()}

        # Receive encrypted updates
        aggregator.receive_encrypted_update(enc_update_1)
        aggregator.receive_encrypted_update(enc_update_2)

        # 3. Aggregate homomorphically
        aggregator.aggregate_encrypted_updates()

        # 4. Verify the global model weights
        # Expected average: [[1.0, 2.0], [3.0, 4.0]]
        expected_weights = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
        actual_weights = global_model.fc.weight.data

        # Allow some tolerance due to possible floating point issues, though noise=0
        torch.testing.assert_close(actual_weights, expected_weights, atol=1e-4, rtol=1e-4)

    def test_meta_abstraction_protocol(self):
        protocol = MetaAbstractionProtocol(initial_level=MetaAbstractionLevel.PHYSICAL)

        # Initial state
        self.assertEqual(protocol.current_level, MetaAbstractionLevel.PHYSICAL)
        self.assertEqual(protocol.coherence, 1.0)

        # Ascend
        protocol.ascend(intensity=0.2)
        self.assertEqual(protocol.current_level, MetaAbstractionLevel.QUANTUM)
        self.assertLess(protocol.coherence, 1.0) # Ascending consumes coherence

        coherence_after_ascend = protocol.coherence

        # Ascend again
        protocol.ascend(intensity=0.1)
        self.assertEqual(protocol.current_level, MetaAbstractionLevel.NEURAL)
        self.assertLess(protocol.coherence, coherence_after_ascend)

        coherence_after_ascend_2 = protocol.coherence

        # Descend
        protocol.descend(intensity=0.5)
        self.assertEqual(protocol.current_level, MetaAbstractionLevel.QUANTUM)
        self.assertGreater(protocol.coherence, coherence_after_ascend_2) # Descending increases coherence

        # Check history
        state = protocol.get_state()
        self.assertEqual(state["transitions_count"], 3)
        self.assertEqual(state["current_level"], "QUANTUM")

if __name__ == '__main__':
    unittest.main()
