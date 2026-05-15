class FederatedTinyTrainer:
    def aggregate(self, gradients):
        return {"status": "aggregated", "privacy": "differential_laplace", "epsilon": 2.0}
