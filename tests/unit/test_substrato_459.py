import unittest
import importlib.util
import os
import sys

class TestSubstrato459(unittest.TestCase):
    def setUp(self):
        module_name = 'substrato_459_hybrid'
        file_path = 'substrates/400-499_advanced/substrato_459_hybrid/substrato_459_hybrid.py'
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = self.module
        spec.loader.exec_module(self.module)

    def test_run_hybrid(self):
        report = self.module.run_hybrid()
        self.assertEqual(report["module"], "459-HYBRID")
        self.assertEqual(report["phi_c"], 0.996)
        self.assertEqual(report["seal"], "c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7")
        self.assertTrue("header_ber" in report)
        self.assertTrue("payload_ber" in report)

if __name__ == '__main__':
    unittest.main()
