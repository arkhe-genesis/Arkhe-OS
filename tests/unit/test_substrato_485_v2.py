import unittest
import importlib.util
import os
import json

class TestSubstrato485V2(unittest.TestCase):
    def setUp(self):
        module_name = "substrato_485_holographic_v2"
        file_path = os.path.join("substrates", "400-499_advanced", "substrato_485_holographic_v2", "substrato_485_holographic_v2.py")
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.substrate = self.module.Substrato485HolographicV2()

    def test_initialization(self):
        self.assertEqual(self.substrate.seal_hash, "b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3")
        self.assertAlmostEqual(self.substrate.phi_c, 0.970)

    def test_canonize(self):
        report_path = self.substrate.canonize()
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, 'r') as f:
            report = json.load(f)

        self.assertIn("SEAL_485_HOLOGRAPHIC_V2", report)
        data = report["SEAL_485_HOLOGRAPHIC_V2"]
        self.assertEqual(data["Hash"], self.substrate.seal_hash)
        self.assertEqual(data["Phi_C"], self.substrate.phi_c)
        self.assertIn("Experimental bulk->boundary projection", data["Features"])

        os.remove(report_path)

if __name__ == "__main__":
    unittest.main()
