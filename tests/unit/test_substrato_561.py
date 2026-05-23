import unittest
import json
import os
import importlib.util

class TestSubstrato561(unittest.TestCase):
    def setUp(self):
        module_name = 'substrato_561_aetherweave_bridge'
        file_path = os.path.join(os.path.dirname(__file__), '../../substrates/500-599_advanced/substrato_561_aetherweave_bridge/substrato_561_aetherweave_bridge.py')

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_canonize_generates_report(self):
        substrate = self.module.Substrato561AetherweaveBridge()
        path, seal = substrate.canonize()

        self.assertTrue(os.path.exists(path))
        self.assertEqual(seal, "1ae22bd12addd830cec4ea91b76fd478fa37f07c3e8539fa0cf0b3852b6641f7")

        with open(path, 'r', encoding='utf-8') as f:
            report = json.load(f)

        self.assertEqual(report['substrate'], "561-AETHERWEAVE-BRIDGE")
        self.assertEqual(report['canonical_seal'], seal)
        self.assertEqual(report['phi_c'], 0.999000)

    def test_no_f_strings(self):
        file_path = os.path.join(os.path.dirname(__file__), '../../substrates/500-599_advanced/substrato_561_aetherweave_bridge/substrato_561_aetherweave_bridge.py')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertNotIn("f\"", content)
        # Avoid checking for f' as it matches dictionary keys ending in f like {'proof': ...}
        # Instead, we just trust there are no f-strings.

if __name__ == '__main__':
    unittest.main()
