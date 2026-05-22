import unittest
import os
import json
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class TestSubstrato514ASIOwlEth(unittest.TestCase):
    def test_canonize_outputs_correct_json(self):
        path = "substrates/400-499_advanced/substrato_514_asi_owl_eth/substrato_514_asi_owl_eth.py"
        module = load_module_from_path("substrato_514", path)
        substrate = module.Substrato514ASIOwlEth()

        out_path = substrate.canonize()
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_514_ASI_OWL_ETH", data)
        self.assertEqual(data["SEAL_514_ASI_OWL_ETH"]["Status"], "CANONIZED (with seal correction)")
        self.assertAlmostEqual(data["SEAL_514_ASI_OWL_ETH"]["Phi_C"], 0.992)
        self.assertEqual(len(data["SEAL_514_ASI_OWL_ETH"]["Features"]), 5)
        self.assertEqual(len(data["SEAL_514_ASI_OWL_ETH"]["Warnings"]), 6)

        # Cleanup
        os.remove(out_path)

if __name__ == '__main__':
    unittest.main()
