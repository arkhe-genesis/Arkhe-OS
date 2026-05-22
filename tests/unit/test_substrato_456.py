import unittest
import importlib.util
import os
import json
import numpy as np

class TestSubstrato456Turbo(unittest.TestCase):
    def setUp(self):
        # Dynamically load the module to avoid SyntaxError due to hyphens in path
        spec = importlib.util.spec_from_file_location(
            "substrato_456_turbo",
            "substrates/400-499_advanced/substrato_456_turbo/substrato_456_turbo.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_turbo_encoder(self):
        encoder = self.module.TurboEncoder(L=4, rate=1/3)
        bits = np.array([1, 0, 1, 1])
        systematic, interleaved = encoder.encode(bits)

        # systematic length should be 3 * len(bits)
        self.assertEqual(len(systematic), 12)
        self.assertEqual(len(interleaved), 12)

        self.assertTrue(all(bit in [0, 1] for bit in systematic))
        self.assertTrue(all(bit in [0, 1] for bit in interleaved))

    def test_canonize(self):
        substrate = self.module.Substrato456Turbo()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_456_TURBO", data)
        self.assertEqual(data["SEAL_456_TURBO"]["Hash"], "07978e0ba40b172f8df890bcee871bb0f2c8ec6598a0c44d69e35110b7dccfee")
        self.assertEqual(data["SEAL_456_TURBO"]["Phi_C"], 0.8910)
        self.assertEqual(data["SEAL_456_TURBO"]["Status"], "CANONIZADO")

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
