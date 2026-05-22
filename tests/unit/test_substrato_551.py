import unittest
import importlib.util
import os
import json

class TestSubstrato551(unittest.TestCase):
    def setUp(self):
        self.script_path = "substrates/500-599_advanced/substrato_551_quantum_foam_sensor/substrato_551_quantum_foam_sensor.py"
        spec = importlib.util.spec_from_file_location("substrato_551_quantum_foam_sensor", self.script_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_canonize_generates_report(self):
        substrate = self.module.Substrato551QuantumFoamSensor()
        path, seal = substrate.canonize()
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(report["phi_c"], 0.999)
        self.assertEqual(report["canonical_seal"], "f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2")
        self.assertEqual(report["substrate"], "551-QUANTUM-FOAM-SENSOR")

    def test_no_f_strings(self):
        with open(self.script_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("f\"", content)
        self.assertNotIn("f'", content)

if __name__ == "__main__":
    unittest.main()
