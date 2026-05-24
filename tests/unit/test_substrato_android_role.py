import unittest
import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class TestSubstratoAndroidRole(unittest.TestCase):
    def test_canonize_outputs_correct_json(self):
        path = "substrates/400-499_advanced/substrato_android_role/substrato_android_role.py"
        module = load_module_from_path("substrato_android_role", path)
        substrate = module.SubstratoAndroidRole()

        out_path = substrate.canonize()
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, 'r') as f:
            data = json.load(f)

        self.assertIn("Title", data)
        self.assertEqual(data["Title"], "Android Experience for Arkhe")
        self.assertIn("Responsibilities", data)
        self.assertEqual(len(data["Responsibilities"]), 7)

        # Cleanup
        os.remove(out_path)

if __name__ == '__main__':
    unittest.main()
