import unittest
import importlib.util
import os
import json

class TestSubstrato515(unittest.TestCase):
    def setUp(self):
        path = "substrates/500-599_advanced/substrato_515_perovskite_qf/substrato_515_perovskite_qf.py"
        spec = importlib.util.spec_from_file_location("substrato_515", path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.substrate = self.module.Substrato515PerovskiteQF()

    def test_no_f_strings(self):
        with open("substrates/500-599_advanced/substrato_515_perovskite_qf/substrato_515_perovskite_qf.py", "r") as f:
            content = f.read()
            self.assertNotIn("f'", content)

    def test_no_non_ascii(self):
        with open("substrates/500-599_advanced/substrato_515_perovskite_qf/substrato_515_perovskite_qf.py", "r") as f:
            content = f.read()
            try:
                content.encode('ascii')
            except UnicodeEncodeError as e:
                self.fail(f"Non-ASCII character found: {e}")

    def test_canonize_output(self):
        path = self.substrate.canonize()
        self.assertTrue(os.path.exists(path))
        with open(path, "r") as f:
            data = json.load(f)
            self.assertEqual(data["id"], "515-PEROVSKITE-QF")
            self.assertEqual(data["canonical_seal"], "05b50293091dfe88f44c4640efe493eefe25d93dfd0c737b6e7047924b0ff59c")
            self.assertEqual(data["phi_c_calculation"]["final_phi_c"], 0.985500)

if __name__ == '__main__':
    unittest.main()
