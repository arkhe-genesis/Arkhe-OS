import unittest
import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class TestSubstrato519_521(unittest.TestCase):
    def test_canonize_outputs_correct_json(self):
        os.environ["ARKHE_SECRET_SEAL"] = "test_seal"
        path = "substrates/500-599_advanced/substrato_519_521_scaled_peace/substrato_519_521_scaled_peace.py"
        module = load_module_from_path("substrato_519_521", path)
        substrate = module.Substrato519_521_ScaledPeace()

        out_path = substrate.canonize()
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, 'r') as f:
            data = json.load(f)

        self.assertIn("phi_c_master", data)
        self.assertEqual(data["phi_c_master"], 0.990)

        # Cleanup
        os.remove(out_path)

if __name__ == '__main__':
    unittest.main()
