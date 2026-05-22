import unittest
import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class TestSubstrato524_526(unittest.TestCase):
    def test_canonize_outputs_correct_json(self):
        path = "substrates/500-599_advanced/substrato_524_526_cathedral_autonomy/substrato_524_526_cathedral_autonomy.py"
        module = load_module_from_path("substrato_524_526", path)
        output_path = module.canonize_524_526_cathedral_autonomy()

        self.assertTrue(os.path.exists(output_path))
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["substrate"], "524-526-CATHEDRAL-AUTONOMY")
        self.assertEqual(data["master_phi_c"], 0.995)

        # Cleanup
        os.remove(output_path)

if __name__ == '__main__':
    unittest.main()
