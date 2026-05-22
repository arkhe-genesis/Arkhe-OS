import unittest
import importlib.util
import os
import sys

class TestSubstrato458(unittest.TestCase):
    def setUp(self):
        module_name = 'substrato_458_adaptive'
        file_path = 'substrates/400-499_advanced/substrato_458_adaptive/substrato_458_adaptive.py'
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = self.module
        spec.loader.exec_module(self.module)

    def test_run_adaptive(self):
        report = self.module.run_adaptive()
        self.assertEqual(report["module"], "458-ADAPTIVE")
        self.assertEqual(report["phi_c"], 0.989)
        self.assertEqual(report["seal"], "b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6")
        self.assertTrue("stats" in report)

if __name__ == '__main__':
    unittest.main()
