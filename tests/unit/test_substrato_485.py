import unittest
import importlib.util
import os
import json
import numpy as np

class TestSubstrato485(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "substrato_485_holographic_projector",
            "substrates/400-499_advanced/substrato_485_holographic_projector/substrato_485_holographic_projector.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_holographic_projector(self):
        kernel = np.random.rand(3, 2)
        proj = self.module.HolographicProjector(alpha_p=0.1, boundary_kernel=kernel)
        bulk = np.random.rand(5, 3)

        projected = proj.project(bulk, 0.5)
        self.assertEqual(projected.shape, (5, 2))

        boundary_obs = np.random.rand(5, 2)
        loss = proj.consistency_loss(bulk, boundary_obs, 0.5)
        self.assertTrue(loss > 0)

    def test_canonize(self):
        substrate = self.module.Substrato485HolographicProjector()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_485_HOLOGRAPHIC_PROJECTOR", data)
        self.assertEqual(data["SEAL_485_HOLOGRAPHIC_PROJECTOR"]["Hash"], "4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5")
        self.assertEqual(data["SEAL_485_HOLOGRAPHIC_PROJECTOR"]["Phi_C"], 0.940)
        self.assertEqual(data["SEAL_485_HOLOGRAPHIC_PROJECTOR"]["Status"], "CANONIZADO")

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
