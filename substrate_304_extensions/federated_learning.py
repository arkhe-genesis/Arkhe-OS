import numpy as np

class FederatedLearningOptimizer:
    def __init__(self, node_count):
        self.node_weights = np.random.rand(node_count)
        self.node_count = node_count

    def optimize_weights(self, historical_phi_c):
        """
        Federated Learning for phi_c weight optimization.
        Uses historical metrics from nodes to optimize coupling weights.
        """
        if not historical_phi_c:
            return self.node_weights

        target_phi_c = 0.95

        # Aggregate historical weights
        avg_history = np.mean(historical_phi_c)
        error = target_phi_c - avg_history

        # Distribute updates based on local performance gradient
        gradient = np.full(self.node_count, error * 0.05)
        self.node_weights += gradient

        # Normalize weights
        self.node_weights = np.clip(self.node_weights, 0.0, 1.0)
        return self.node_weights
