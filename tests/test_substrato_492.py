import unittest
import os
import json
import importlib.util
import sys

class TestSubstrato492(unittest.TestCase):
    def setUp(self):
        # Dynamically load the module
        module_name = "substrato_492_kagome_kondo"
        file_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "substrates",
            "400-499_advanced",
            "substrato_492_kagome_kondo",
            "substrato_492_kagome_kondo.py"
        )
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = self.module
        spec.loader.exec_module(self.module)

    def test_canonize(self):
        substrate = self.module.Substrato492KagomeKondo()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["Substrate"], "492-KAGOME-KONDO")
        self.assertEqual(data["Phi_C"], 0.975)
        self.assertEqual(data["Principle_XI"], "Correlation")

        # Clean up
        os.remove(path)

if __name__ == '__main__':
    unittest.main()
