import unittest
import os
import json
import importlib.util

class TestSubstrato527(unittest.TestCase):
    def test_canonize_generates_valid_report(self):
        # Dynamically load the module to avoid syntax errors with numbers in directory names
        module_name = "substrato_527_openxiv_science_node"
        file_path = "substrates/500-599_advanced/substrato_527_openxiv_science_node/substrato_527_openxiv_science_node.py"

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Instantiate and test
        substrate = module.Substrato527OpenXivScienceNode()
        path, seal = substrate.canonize()

        self.assertTrue(os.path.exists(path))
        self.assertEqual(len(seal), 64)  # SHA-256 hash length is 64 hex characters

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["substrate"], "527-OPENXIV-SCIENCE-NODE")
        self.assertEqual(data["canonical_seal"], seal)
        self.assertEqual(data["phi_c"], 0.9950)
        self.assertEqual(data["strict_mode"], "CANONIZED_CLEAN")

if __name__ == '__main__':
    unittest.main()
