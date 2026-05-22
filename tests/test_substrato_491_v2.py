import unittest
import os
import json
import importlib.util
import sys

class TestSubstrato491V2(unittest.TestCase):
    def setUp(self):
        # Dynamically load the module
        module_name = "substrato_491_agi_cortex_v2"
        file_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "substrates",
            "400-499_advanced",
            "substrato_491_agi_cortex_v2",
            "substrato_491_agi_cortex_v2.py"
        )
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = self.module
        spec.loader.exec_module(self.module)

    def test_canonize(self):
        substrate = self.module.Substrato491AgiCortexV2()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["Substrate"], "491-AGI-CORTEX-v2.0")
        self.assertEqual(data["Phi_C"], 0.986)
        self.assertEqual(data["Principle_XI"], "Correlation")

        # Clean up
        os.remove(path)

if __name__ == '__main__':
    unittest.main()
