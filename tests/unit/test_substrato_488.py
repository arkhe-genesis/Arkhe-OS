import unittest
import importlib.util
import os
import json

class TestSubstrato488(unittest.TestCase):
    def setUp(self):
        module_name = "substrato_488_photonic_gyrotron"
        file_path = os.path.join("substrates", "400-499_advanced", "substrato_488_photonic_gyrotron", "substrato_488_photonic_gyrotron.py")
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.substrate = self.module.Substrato488PhotonicGyrotron()

    def test_initialization(self):
        self.assertEqual(self.substrate.seal_hash, "c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5")
        self.assertAlmostEqual(self.substrate.phi_c, 0.950)

    def test_canonize(self):
        report_path = self.substrate.canonize()
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, 'r') as f:
            report = json.load(f)

        self.assertIn("SEAL_488_PHOTONIC_GYROTRON", report)
        data = report["SEAL_488_PHOTONIC_GYROTRON"]
        self.assertEqual(data["Hash"], self.substrate.seal_hash)
        self.assertEqual(data["Phi_C"], self.substrate.phi_c)
        self.assertIn("Initial_State", data["Simulation"])
        self.assertIn("Final_State", data["Simulation"])

        os.remove(report_path)

if __name__ == "__main__":
    unittest.main()
