import unittest
import importlib.util
import os
import json

class TestSubstrato555(unittest.TestCase):
    def setUp(self):
        self.script_path = "substrates/500-599_advanced/substrato_555_helical_invariant_theory/substrato_555_helical_invariant_theory.py"
        spec = importlib.util.spec_from_file_location("substrato_555_helical_invariant_theory", self.script_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_canonize_generates_report(self):
        substrate = self.module.Substrato555HelicalInvariantTheory()
        path, seal = substrate.canonize()
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            report = json.load(f)
        self.assertEqual(report["phi_c"], 0.947)
        self.assertEqual(report["canonical_seal"], "f082eba4348123568c4689649ee14a4675596eb33370e162b446cb6df42fd5c4")
        self.assertEqual(report["substrate"], "555-HELICAL-INVARIANT-THEORY")

    def test_no_f_strings(self):
        with open(self.script_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("f\"", content)
        self.assertNotIn("f'", content)

if __name__ == "__main__":
    unittest.main()
