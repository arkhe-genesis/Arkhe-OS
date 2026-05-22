import unittest
import importlib.util
import os
import json

class TestSubstrato540(unittest.TestCase):
    def setUp(self):
        self.script_path = "substrates/500-599_advanced/substrato_540_hamiltonian_inference/substrato_540_hamiltonian_inference.py"
        spec = importlib.util.spec_from_file_location("substrato_540_hamiltonian_inference", self.script_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_canonize_generates_report(self):
        substrate = self.module.Substrato540HamiltonianInference()
        path, seal = substrate.canonize()
        self.assertTrue(os.path.exists(path))
        with open(path, "r") as f:
            report = json.load(f)
        self.assertEqual(report["phi_c"], 0.985)
        self.assertIn("canonical_seal", report)

    def test_no_f_strings_or_non_ascii(self):
        with open(self.script_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("f\"", content)
        self.assertNotIn("f'", content)
        try:
            content.encode("ascii")
        except UnicodeEncodeError:
            self.fail("File contains non-ASCII characters")

if __name__ == "__main__":
    unittest.main()
