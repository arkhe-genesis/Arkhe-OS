import unittest
import importlib.util
import os
import json

class TestSubstrato487(unittest.TestCase):
    def setUp(self):
        # Dynamically load the module due to hyphen in path
        module_name = "substrato_487_photonic_crystal"
        file_path = os.path.join("substrates", "400-499_advanced", "substrato_487_photonic_crystal", "substrato_487_photonic_crystal.py")
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.substrate = self.module.Substrato487PhotonicCrystal()

    def test_initialization(self):
        self.assertEqual(self.substrate.seal_hash, "a4f7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5")
        self.assertAlmostEqual(self.substrate.phi_c, 0.985)
        self.assertEqual(self.substrate.material, "TiO2 nanopillars")
        self.assertEqual(self.substrate.period_nm, 360)

    def test_canonize(self):
        report_path = self.substrate.canonize()
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, 'r') as f:
            report = json.load(f)

        self.assertIn("SEAL_487_PHOTONIC_CRYSTAL", report)
        data = report["SEAL_487_PHOTONIC_CRYSTAL"]
        self.assertEqual(data["Hash"], self.substrate.seal_hash)
        self.assertEqual(data["Phi_C"], self.substrate.phi_c)
        self.assertEqual(data["Material"], self.substrate.material)
        self.assertEqual(data["Period_nm"], self.substrate.period_nm)
        self.assertIn("BIC Q -> infinity", data["Features"])
        self.assertIn("Topological phase 2*pi", data["Features"])
        self.assertIn("Local-nonlocal duality validated", data["Features"])

        # Cleanup
        os.remove(report_path)

if __name__ == "__main__":
    unittest.main()
