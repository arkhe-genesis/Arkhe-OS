import unittest
import json
import importlib.util
import sys
import os

class TestSubstrato534536(unittest.TestCase):
    def setUp(self):
        # Add the directory to sys.path so 'import invariants' works
        sys.path.insert(0, os.path.abspath('substrates/500-599_advanced/substrato_534_536_resonance_chain'))

        spec_decree = importlib.util.spec_from_file_location("canonization_decree", "substrates/500-599_advanced/substrato_534_536_resonance_chain/canonization_decree.py")
        self.decree_module = importlib.util.module_from_spec(spec_decree)
        spec_decree.loader.exec_module(self.decree_module)

        spec_bus = importlib.util.spec_from_file_location("analog_bus_interface", "substrates/500-599_advanced/substrato_534_536_resonance_chain/analog_bus_interface.py")
        self.bus_module = importlib.util.module_from_spec(spec_bus)
        spec_bus.loader.exec_module(self.bus_module)

    def tearDown(self):
        sys.path.pop(0)

    def test_decree_output(self):
        path = self.decree_module.execute()
        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("decree", data)
        self.assertIn("master_phi_c", data)
        self.assertEqual(data["master_invariants"], "18/18 PASS")

        components = [c['id'] for c in data['components']]
        self.assertIn("534-BRODMANN-GELS", components)
        self.assertIn("535-DODECANOGRAM", components)
        self.assertIn("536-GRAND-RESONANCE-CHAIN", components)
        self.assertIn("Principle XVIII", components)

    def test_bus_interface(self):
        path = self.bus_module.execute()
        with open(path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["spec"], "Analog Bus Interface Specification")
        self.assertEqual(data["data"]["source"], "534-BRODMANN-GELS")
        self.assertEqual(data["data"]["target"], "501-AI-KERNEL")

if __name__ == '__main__':
    unittest.main()
