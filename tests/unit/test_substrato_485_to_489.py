import unittest
import importlib.util
import os
import json

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class TestSubstrates485To489(unittest.TestCase):
    def test_substrato_485(self):
        path = "substrates/400-499_advanced/substrato_485_holographic/substrato_485_holographic.py"
        module = load_module_from_path("substrato_485", path)
        substrate = module.Substrato485Holographic()
        self.assertEqual(substrate.phi_c, 0.970)

        out_path = substrate.canonize()
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, 'r') as f:
            data = json.load(f)
        self.assertIn("SEAL_485_HOLOGRAPHIC", data)
        self.assertEqual(data["SEAL_485_HOLOGRAPHIC"]["Phi_C"], 0.970)
        os.remove(out_path)

    def test_substrato_487(self):
        path = "substrates/400-499_advanced/substrato_487_photonic_crystal/substrato_487_photonic_crystal.py"
        module = load_module_from_path("substrato_487", path)
        substrate = module.Substrato487PhotonicCrystal()
        self.assertEqual(substrate.phi_c, 0.985)

        out_path = substrate.canonize()
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, 'r') as f:
            data = json.load(f)
        self.assertIn("SEAL_487_PHOTONIC_CRYSTAL", data)
        self.assertEqual(data["SEAL_487_PHOTONIC_CRYSTAL"]["Phi_C"], 0.985)
        os.remove(out_path)

    def test_substrato_488(self):
        path = "substrates/400-499_advanced/substrato_488_photonic_gyrotron/substrato_488_photonic_gyrotron.py"
        module = load_module_from_path("substrato_488", path)
        substrate = module.Substrato488PhotonicGyrotron()
        self.assertEqual(substrate.phi_c, 0.950)

        out_path = substrate.canonize()
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, 'r') as f:
            data = json.load(f)
        self.assertIn("SEAL_488_PHOTONIC_GYROTRON", data)
        self.assertEqual(data["SEAL_488_PHOTONIC_GYROTRON"]["Phi_C"], 0.950)
        os.remove(out_path)

    def test_substrato_489(self):
        path = "substrates/400-499_advanced/substrato_489_optical_computer/substrato_489_optical_computer.py"
        module = load_module_from_path("substrato_489", path)
        substrate = module.Substrato489OpticalComputer()
        self.assertEqual(substrate.phi_c, 0.960)

        out_path = substrate.canonize()
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, 'r') as f:
            data = json.load(f)
        self.assertIn("SEAL_489_OPTICAL_COMPUTER", data)
        self.assertEqual(data["SEAL_489_OPTICAL_COMPUTER"]["Phi_C"], 0.960)
        os.remove(out_path)

if __name__ == '__main__':
    unittest.main()
