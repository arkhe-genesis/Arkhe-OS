import unittest
import importlib.util
import os
import json
import numpy as np

class TestSubstrato483(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "substrato_483_ensemble_aggregator",
            "substrates/400-499_advanced/substrato_483_ensemble_aggregator/substrato_483_ensemble_aggregator.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

        spec_opt = importlib.util.spec_from_file_location(
            "substrato_482_qubo_optimizer",
            "substrates/400-499_advanced/substrato_482_qubo_optimizer/substrato_482_qubo_optimizer.py"
        )
        self.module_opt = importlib.util.module_from_spec(spec_opt)
        spec_opt.loader.exec_module(self.module_opt)

    def test_ensemble(self):
        agg = self.module.EnsembleAggregator(n_learners=2)
        opt = self.module_opt.QUBOOptimizer(use_hardware=False)
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([1, -1, 1, -1])
        # Need to provide more samples to balanced_sample than it asks,
        # but for this mock we just call train_bagging, it will use its own dummy sampling

        # overriding the dummy sample inside the test for predictability
        agg._balanced_sample = lambda labels, n: np.arange(len(labels))

        agg.train_bagging(X, y, opt)
        self.assertEqual(len(agg.learners), 2)

        preds = agg.predict(X)
        self.assertEqual(len(preds), 4)

    def test_canonize(self):
        substrate = self.module.Substrato483EnsembleAggregator()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_483_ENSEMBLE_AGGREGATOR", data)
        self.assertEqual(data["SEAL_483_ENSEMBLE_AGGREGATOR"]["Hash"], "2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3")
        self.assertEqual(data["SEAL_483_ENSEMBLE_AGGREGATOR"]["Phi_C"], 0.980)
        self.assertEqual(data["SEAL_483_ENSEMBLE_AGGREGATOR"]["Status"], "CANONIZADO")

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
