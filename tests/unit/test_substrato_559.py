import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import importlib.util

class TestSubstrato559(unittest.TestCase):
    def setUp(self):
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../substrates/500-599_advanced/substrato_559_ecosystem_braid/substrato_559_ecosystem_braid.py"))
        spec = importlib.util.spec_from_file_location("substrato_559_ecosystem_braid", file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_canonize_generates_report(self):
        substrate = self.module.Substrato559EcosystemBraid()
        json_path = substrate.canonize()
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data["phi_c"], 0.999000)
        self.assertIn("canonical_seal", data)
        self.assertEqual(data["substrate"], "559-ECOSYSTEM-BRAID")
        os.remove(json_path)

    def test_no_f_strings(self):
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../substrates/500-599_advanced/substrato_559_ecosystem_braid/substrato_559_ecosystem_braid.py"))
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("f\"", content)
        self.assertNotIn("f'", content)

if __name__ == '__main__':
    unittest.main()
