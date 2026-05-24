import unittest
import importlib.util
import os
import json

class TestSubstrato489(unittest.TestCase):
    def setUp(self):
        module_name = "substrato_489_optical_computer"
        file_path = os.path.join("substrates", "400-499_advanced", "substrato_489_optical_computer", "substrato_489_optical_computer.py")
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.substrate = self.module.Substrato489OpticalComputer()

    def test_initialization(self):
        self.assertEqual(self.substrate.seal_hash, "d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
        self.assertAlmostEqual(self.substrate.phi_c, 0.960)

    def test_canonize(self):
        report_path = self.substrate.canonize()
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, 'r') as f:
            report = json.load(f)

        self.assertIn("SEAL_489_OPTICAL_COMPUTER", report)
        data = report["SEAL_489_OPTICAL_COMPUTER"]
        self.assertEqual(data["Hash"], self.substrate.seal_hash)
        self.assertEqual(data["Phi_C"], self.substrate.phi_c)
        self.assertIn("Simulation", data)
        self.assertIn("Input", data["Simulation"])
        self.assertIn("Output", data["Simulation"])

        os.remove(report_path)

if __name__ == "__main__":
    unittest.main()
