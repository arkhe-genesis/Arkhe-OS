import unittest
import importlib.util
import os
import json
import numpy as np

class TestSubstrato455Polar(unittest.TestCase):
    def setUp(self):
        # Dynamically load the module to avoid SyntaxError due to hyphens in path
        spec = importlib.util.spec_from_file_location(
            "substrato_455_polar",
            "substrates/400-499_advanced/substrato_455_polar/substrato_455_polar.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_polar_encoder(self):
        encoder = self.module.PolarEncoder(N=4, K=2)
        bits = np.array([1, 0])
        encoded = encoder.encode(bits)
        self.assertEqual(len(encoded), 4)
        self.assertTrue(all(bit in [0, 1] for bit in encoded))

    def test_canonize(self):
        substrate = self.module.Substrato455Polar()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_455_POLAR", data)
        self.assertEqual(data["SEAL_455_POLAR"]["Hash"], "444dbdfe7e76de88f4f1ef978b2759b0955821e22ab0bfc88fa1243cb92a174e")
        self.assertEqual(data["SEAL_455_POLAR"]["Phi_C"], 0.9050)
        self.assertEqual(data["SEAL_455_POLAR"]["Status"], "CANONIZADO")

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
