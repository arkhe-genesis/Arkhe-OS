import unittest
import os
import json
import importlib.util

class TestSubstrato522(unittest.TestCase):
    def test_canonize_outputs_correct_json(self):
        file_path = "substrates/500-599_advanced/substrato_522_nato_climate_node/substrato_522_nato_climate_node.py"
        spec = importlib.util.spec_from_file_location("substrato_522", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        output_path = module.canonize_522_nato_climate_node()
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["substrate"], "522-NATO-CLIMATE-NODE")
        self.assertEqual(data["phi_c"], 0.987)
        self.assertEqual(data["sha_256"], "e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2")

        os.remove(output_path)

if __name__ == "__main__":
    unittest.main()
