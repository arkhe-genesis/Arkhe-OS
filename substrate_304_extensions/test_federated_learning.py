import unittest
import numpy as np
from federated_learning import FederatedLearningOptimizer

class TestFederatedLearning(unittest.TestCase):
    def test_optimization(self):
        optimizer = FederatedLearningOptimizer(10)
        initial_weights = optimizer.node_weights.copy()

        # Mock low history to test gradient boost
        new_weights = optimizer.optimize_weights([0.5, 0.6, 0.7])

        self.assertEqual(len(new_weights), 10)
        self.assertTrue(np.all(new_weights > initial_weights))

if __name__ == "__main__":
    unittest.main()
