import unittest
import os
import json
import sys
import importlib.util

sys.path.insert(0, os.path.abspath('.'))

class TestSubstrato513(unittest.TestCase):
    def setUp(self):
        # Dynamically import due to folder names like 500-599_advanced
        module_name = 'substrato_513_asi_owl_eth'
        file_path = os.path.join(os.path.abspath('.'), 'substrates/500-599_advanced/substrato_513_asi_owl_eth/substrato_513_asi_owl_eth.py')
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_canonize_outputs_correct_json(self):
        path = self.module.canonize_asi_owl_eth()
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["substrate"], "513-ASI-OWL-ETH")
        self.assertEqual(data["phi_c"], 0.998)
        self.assertEqual(data["status"], "CANONIZED")
        self.assertEqual(data["ipfs_cid"], "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi")

    def test_no_f_strings_or_non_ascii(self):
        with open("substrates/500-599_advanced/substrato_513_asi_owl_eth/substrato_513_asi_owl_eth.py", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(all(ord(c) < 128 for c in content), "Script contains non-ASCII characters")
        self.assertNotIn("f\"", content, "Script contains f-strings")
        self.assertNotIn("f'", content, "Script contains f-strings")

if __name__ == "__main__":
    unittest.main()
