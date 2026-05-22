import unittest
import os
import json
import importlib.util

class TestSubstrato547(unittest.TestCase):
    def test_canonize_generates_valid_report(self):
        # Dynamically load the module to avoid syntax errors with numbers in directory names
        module_name = "substrato_547_ipns_core"
        file_path = "substrates/500-599_advanced/substrato_547_ipns_core/substrato_547_ipns_core.py"

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Instantiate and test
        substrate = module.Substrato547IPNSCore()
        path, seal = substrate.canonize()

        self.assertTrue(os.path.exists(path))
        self.assertEqual(seal, "b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9")
        self.assertEqual(len(seal), 64)  # SHA-256 hash length is 64 hex characters

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["substrate"], "547-IPNS-CORE")
        self.assertEqual(data["canonical_seal"], seal)
        self.assertEqual(data["phi_c"], 0.998)
        self.assertEqual(data["ipns_key"], "k51qzi5uqu5dlxgpwjkkiyqik8btk7pa07y76ca7zy8mqse6i5bzjukmivefwe")
        self.assertEqual(data["strict_mode"], "CANONIZED_CLEAN")

if __name__ == '__main__':
    unittest.main()
