import unittest
import importlib.util
import os
import json
import numpy as np

class TestSubstrato486(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "substrato_486_hybrid_accelerator",
            "substrates/400-499_advanced/substrato_486_hybrid_accelerator/substrato_486_hybrid_accelerator.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_accelerator(self):
        acc = self.module.HybridAccelerator()
        # test the dummy methods
        res = acc._picard_step(5.0)
        self.assertEqual(res, 5.1)

        qk = acc.quantum_kernel([1, 2, 3], [4, 5, 6])
        self.assertEqual(len(qk), 5)

        jp = acc.jax_ensemble_predict([2.0, 4.0], None)
        self.assertTrue(np.array_equal(jp, [1.0, 2.0]))

    def test_canonize(self):
        substrate = self.module.Substrato486HybridAccelerator()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_486_HYBRID_ACCELERATOR", data)
        self.assertEqual(data["SEAL_486_HYBRID_ACCELERATOR"]["Hash"], "5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6")
        self.assertEqual(data["SEAL_486_HYBRID_ACCELERATOR"]["Phi_C"], 0.920)
        self.assertEqual(data["SEAL_486_HYBRID_ACCELERATOR"]["Status"], "CANONIZADO")

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
