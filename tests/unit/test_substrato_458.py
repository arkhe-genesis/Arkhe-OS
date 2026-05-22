import unittest
import importlib.util
import os
import json

class TestSubstrato458Adaptive(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "substrato_458_adaptive",
            "substrates/400-499_advanced/substrato_458_adaptive/substrato_458_adaptive.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_snr_selector(self):
        selector = self.module.SNRSelector()
        self.assertEqual(selector.select_code(1.0), "456-TURBO")
        self.assertEqual(selector.select_code(4.0), "459-HYBRID")
        self.assertEqual(selector.select_code(6.0), "455-POLAR")
        self.assertEqual(selector.select_code(10.0), "451-CYCLIC")

    def test_canonize(self):
        substrate = self.module.Substrato458Adaptive()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as f:
            data = json.load(f)
        self.assertIn("SEAL_458_ADAPTIVE", data)
        os.remove(path)

if __name__ == '__main__':
    unittest.main()
