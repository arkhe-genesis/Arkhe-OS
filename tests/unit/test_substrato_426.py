import os
import json
import unittest
import sys
import importlib.util

# Load module from path because of hyphens in directory name
module_name = 'substrato_426_blue_lattice'
module_path = 'substrates/400-499_advanced/substrato_426_blue_lattice/substrato_426_blue_lattice.py'
spec = importlib.util.spec_from_file_location(module_name, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module
spec.loader.exec_module(module)
Substrato426BlueLattice = module.Substrato426BlueLattice

class TestSubstrato426(unittest.TestCase):
    def test_canonize_outputs_correct_json(self):
        substrate = Substrato426BlueLattice()
        path = substrate.canonize()

        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("SEAL_426_BLUE_LATTICE_V2", data)
        seal = data["SEAL_426_BLUE_LATTICE_V2"]

        self.assertEqual(seal["Hash"], "8bbda8762076b360e8e2e8c8d8f8a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5")
        self.assertEqual(seal["Phi_C"], 0.9990)
        self.assertEqual(seal["Vertices"], 625)
        self.assertEqual(seal["Arestas"], 9350)
        self.assertEqual(seal["Grau_Medio"], 29.9)
        self.assertEqual(seal["Simetria"], "D6 preservada")
        self.assertEqual(seal["Status"], "CANONIZADO")

        os.remove(path)

if __name__ == "__main__":
    unittest.main()
