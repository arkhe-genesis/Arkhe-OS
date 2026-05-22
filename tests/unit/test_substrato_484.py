import unittest
import importlib.util
import os
import json
import numpy as np

class TestSubstrato484(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "substrato_484_lattice_simulator",
            "substrates/400-499_advanced/substrato_484_lattice_simulator/substrato_484_lattice_simulator.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_lattice(self):
        # Use a small N for testing to avoid huge memory footprint
        sim = self.module.HVFFLatticeSimulator(N=100)
        initial_u = sim.u.copy()
        sim.picard_step()
        self.assertFalse(np.array_equal(sim.u, initial_u))

        feats = sim.extract_features()
        self.assertEqual(feats.shape, (100, 5))

    def test_canonize(self):
        substrate = self.module.Substrato484LatticeSimulator()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_484_LATTICE_SIMULATOR", data)
        self.assertEqual(data["SEAL_484_LATTICE_SIMULATOR"]["Hash"], "3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4")
        self.assertEqual(data["SEAL_484_LATTICE_SIMULATOR"]["Phi_C"], 0.990)
        self.assertEqual(data["SEAL_484_LATTICE_SIMULATOR"]["Status"], "CANONIZADO")

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
