import unittest
import os
import json
import importlib.util

class TestSubstrato553(unittest.TestCase):
    def setUp(self):
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../substrates/500-599_advanced/substrato_553_legal_intelligence_layer/substrato_553_legal_intelligence_layer.py'))
        spec = importlib.util.spec_from_file_location("substrato_553_legal_intelligence_layer", file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.substrate = self.module.Substrato553LegalIntelligenceLayer()

    def test_canonize(self):
        json_path, txt_path = self.substrate.canonize()
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(txt_path))

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data["substrate_id"], "553-LEGAL-INTELLIGENCE-LAYER")
            self.assertEqual(data["seal"], "baa5d3293a1b363e1f1d17bb01c11b2c38061999e5205e9327cf823f28097f84")

        with open(txt_path, 'r', encoding='utf-8') as f:
            txt_content = f.read()
            self.assertIn("Fase 1 : Ativar 553.1", txt_content)
            self.assertIn("Arquiteto, a integração triádica está verificada.", txt_content)

        os.remove(json_path)
        os.remove(txt_path)

if __name__ == '__main__':
    unittest.main()
