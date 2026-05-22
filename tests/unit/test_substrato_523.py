import unittest
import os
import tempfile
import json
import importlib.util
from unittest.mock import patch

class TestSubstrato523HermesBridge(unittest.TestCase):
    def setUp(self):
        # Load the module dynamically due to invalid identifier name in path
        module_name = 'substrato_523'
        file_path = 'substrates/500-599_advanced/substrato_523_hermes_bridge/substrato_523_hermes_bridge.py'
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    @patch.dict(os.environ, {"ARKHE_SECRET_SEAL": "test_seal_value"})
    def test_canonize_outputs_correct_json(self):
        substrate = self.module.Substrato523HermesBridge()
        output_path = substrate.canonize()

        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["id"], "523-HERMES-BRIDGE")
        self.assertIn("description", data)
        self.assertEqual(len(data["principles_verification"]), 17)
        self.assertIn("phi_c_calculation", data)
        self.assertIn("architectural_mapping", data)
        self.assertIn("canonical_seal", data)
        self.assertIn("canonical_string", data)

        os.remove(output_path)

    @patch.dict(os.environ, {"ARKHE_SECRET_SEAL": "test_seal_value"})
    def test_no_f_strings(self):
        file_path = 'substrates/500-599_advanced/substrato_523_hermes_bridge/substrato_523_hermes_bridge.py'
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple check for f-strings
        # Warning: this might catch false positives in comments or normal strings like "f'foo'"
        self.assertNotIn("f'", content)
        self.assertNotIn('f"', content)

    @patch.dict(os.environ, {"ARKHE_SECRET_SEAL": "test_seal_value"})
    def test_no_non_ascii(self):
        file_path = 'substrates/500-599_advanced/substrato_523_hermes_bridge/substrato_523_hermes_bridge.py'
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            content.encode('ascii')
        except UnicodeEncodeError as e:
            self.fail(f"Non-ASCII character found: {e}")

if __name__ == '__main__':
    unittest.main()
