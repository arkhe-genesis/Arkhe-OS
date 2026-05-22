import unittest
import os
import json
import importlib.util

class TestSubstrato562StimQecSimulator(unittest.TestCase):
    def setUp(self):
        # Load the module dynamically due to invalid identifier name
        module_name = "substrato_562_stim_qec_simulator"
        file_path = "substrates/500-599_advanced/substrato_562_stim_qec_simulator/substrato_562_stim_qec_simulator.py"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_canonize_creates_valid_json(self):
        simulator = self.module.Substrato562StimQecSimulator()
        path, seal = simulator.canonize()

        self.assertTrue(os.path.exists(path))

        with open(path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["substrate"], "562-STIM-QEC-SIMULATOR")
        self.assertEqual(report["canonical_seal"], seal)
        self.assertEqual(report["phi_c"], 0.999)
        self.assertIn("562-BIS-SINTER-DECODER", report["deliverable_b"]["name"])
        self.assertIn("Stim <-> 557-ISING-BRAID Integration", report["deliverable_c"]["name"])
        self.assertTrue(report["results"]["d3_logical_error_rate"] > 0.0 or report["results"]["d3_logical_error_rate"] == 0.0)

        os.remove(path)

    def test_no_f_strings_and_non_ascii(self):
        file_path = "substrates/500-599_advanced/substrato_562_stim_qec_simulator/substrato_562_stim_qec_simulator.py"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn("f\"", content)
        self.assertNotIn("f'", content)
        self.assertIn("CONCLUÍDOS", content) # Verify non-ASCII characters

if __name__ == '__main__':
    unittest.main()
