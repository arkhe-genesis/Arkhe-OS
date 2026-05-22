import unittest
import os
import sys
import importlib.util
import json

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

class TestSubstrato519521(unittest.TestCase):
    def setUp(self):
        self.path = "substrates/500-599_advanced/substrato_519_521_ssi_triad/substrato_519_521_ssi_triad.py"
        self.module = load_module_from_path("substrato_519_521", self.path)

    def test_invariants_no_f_strings(self):
        with open(self.path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("f\"", content)
        self.assertNotIn("f'", content)

    def test_invariants_no_non_ascii(self):
        with open(self.path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(all(ord(c) < 128 for c in content))

    def test_canonize_outputs_correct_json(self):
        substrate = self.module.Substrato519521SSITriad()
        temp_file = substrate.canonize()

        self.assertTrue(os.path.exists(temp_file))

        with open(temp_file, "r") as f:
            data = json.load(f)

        self.assertEqual(data["triad_id"], "519-521")
        self.assertEqual(data["status"], "STRICT_MODE|CANONIZED_CLEAN")

        os.remove(temp_file)

if __name__ == "__main__":
    unittest.main()
