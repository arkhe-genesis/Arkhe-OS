import unittest
import importlib.util
import os
import json
import numpy as np

class TestSubstrato459Hybrid(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "substrato_459_hybrid",
            "substrates/400-499_advanced/substrato_459_hybrid/substrato_459_hybrid.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_hybrid_encoder(self):
        encoder = self.module.HybridEncoder()
        bits = np.array([1, 0])

        res1 = encoder.encode(bits, 2.0)
        self.assertEqual(res1["type"], "TURBO_ONLY")

        res2 = encoder.encode(bits, 7.0)
        self.assertEqual(res2["type"], "POLAR_ONLY")

        res3 = encoder.encode(bits, 4.0)
        self.assertEqual(res3["type"], "POLAR_TURBO_CONCATENATED")

    def test_canonize(self):
        substrate = self.module.Substrato459Hybrid()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as f:
            data = json.load(f)
        self.assertIn("SEAL_459_HYBRID", data)
        os.remove(path)

if __name__ == '__main__':
    unittest.main()
