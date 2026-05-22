import unittest
import importlib.util
import os
import json
import numpy as np

class TestSubstrato482(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "substrato_482_qubo_optimizer",
            "substrates/400-499_advanced/substrato_482_qubo_optimizer/substrato_482_qubo_optimizer.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_optimizer_simulated(self):
        opt = self.module.QUBOOptimizer(use_hardware=False)
        X = np.array([[1, 2], [3, 4]])
        y = np.array([1, -1])
        res = opt.solve_svm_qubo(X, y)
        self.assertIsNotNone(res)

    def test_canonize(self):
        substrate = self.module.Substrato482QuboOptimizer()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_482_QUBO_OPTIMIZER", data)
        self.assertEqual(data["SEAL_482_QUBO_OPTIMIZER"]["Hash"], "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2")
        self.assertEqual(data["SEAL_482_QUBO_OPTIMIZER"]["Phi_C"], 0.950)
        self.assertEqual(data["SEAL_482_QUBO_OPTIMIZER"]["Status"], "CANONIZADO")

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
