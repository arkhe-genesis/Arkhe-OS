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

class TestSubstrato523(unittest.TestCase):
    def setUp(self):
        self.path = "substrates/500-599_advanced/substrato_523_hermes_bridge/substrato_523_hermes_bridge.py"
        self.module = load_module_from_path("substrato_523", self.path)

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
        substrate = self.module.Substrato523HermesBridge()
        temp_file = substrate.canonize()

        self.assertTrue(os.path.exists(temp_file))

        with open(temp_file, "r") as f:
            data = json.load(f)

        self.assertEqual(data["substrate_id"], "523-HERMES-BRIDGE")
        self.assertEqual(data["status"], "STRICT_MODE|CANONIZED_CLEAN")

        os.remove(temp_file)

if __name__ == "__main__":
    unittest.main()
