import unittest
import os
import json
import importlib.util

class TestSubstrato552(unittest.TestCase):
    def setUp(self):
        # Dynamically load the module due to invalid identifier name in path (500-599_advanced)
        path = os.path.join("substrates", "500-599_advanced", "substrato_552_legal_intelligence", "substrato_552_legal_intelligence.py")
        spec = importlib.util.spec_from_file_location("substrato_552_legal_intelligence", path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_canonize_output(self):
        substrate = self.module.Substrato552LegalIntelligence()
        path, canonical_seal = substrate.canonize()

        self.assertEqual(canonical_seal, "18f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c4b3a2918f7")
        self.assertTrue(os.path.exists(path))

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data["substrate"], "552-LEGAL-INTELLIGENCE")
        self.assertEqual(data["canonical_seal"], canonical_seal)
        self.assertEqual(data["phi_c"], 0.981)
        self.assertEqual(data["status"], "CANONIZED_CLEAN")
        self.assertIn("Ω", data["title"])
        self.assertEqual(data["consolidation"]["Adjusted_Phi_C"], 0.981)
        self.assertIn("552.1", data["modules"])
        self.assertIn("552.6", data["modules"])

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
