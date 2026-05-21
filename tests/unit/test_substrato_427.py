import os
import json
import unittest
import sys
import importlib.util

# Load module from path because of hyphens in directory name
module_name = 'substrato_427_blue_chromatic'
module_path = 'substrates/400-499_advanced/substrato_427_blue_chromatic/substrato_427_blue_chromatic.py'
spec = importlib.util.spec_from_file_location(module_name, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module
spec.loader.exec_module(module)
Substrato427BlueChromatic = module.Substrato427BlueChromatic

class TestSubstrato427(unittest.TestCase):
    def test_canonize_outputs_correct_json(self):
        substrate = Substrato427BlueChromatic()
        path = substrate.canonize()

        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_427_BLUE_CHROMATIC_V2", data)
        seal = data["SEAL_427_BLUE_CHROMATIC_V2"]

        self.assertEqual(seal["Hash"], "79895ffca452b983a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4")
        self.assertEqual(seal["Phi_C"], 0.8182)
        self.assertEqual(seal["Cores"], 16)
        self.assertEqual(seal["Triangulos"], 35050)
        self.assertEqual(seal["Modos_Coerencia"], "E_J, E_coup, k_B T, SQUID")
        self.assertEqual(seal["Conjectura_Bruijn_Erdos"], "chi >= 4 satisfeito (chi = 16 >= 4)")
        self.assertEqual(seal["Status"], "CANONIZADO")

        os.remove(path)

if __name__ == "__main__":
    unittest.main()
