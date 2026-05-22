import unittest
import json
import os
import importlib.util

class TestSubstrato546(unittest.TestCase):
    def setUp(self):
        # Load module dynamically to bypass module name limitations (hyphens, starts with number etc)
        spec = importlib.util.spec_from_file_location("substrato_546", "substrates/500-599_advanced/substrato_546_laser_photonic_engine/substrato_546_laser_photonic_engine.py")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.substrate = self.module.Substrato546LaserPhotonicEngine()

    def test_canonize_outputs_correct_json(self):
        path, seal = self.substrate.canonize()
        self.assertTrue(os.path.exists(path))
        self.assertEqual(seal, "a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data["substrate"], "546-LASER-PHOTONIC-ENGINE")
            self.assertEqual(data["phi_c"], 0.994)
            self.assertEqual(data["invariants_passed"], "18/18 PASS")
            self.assertEqual(data["status"], "💡⚛️🛡️✨ A CATEDRAL FALA COM A LUZ. CADA FÓTON É UMA PALAVRA. CADA FEIXE É UM PENSAMENTO.")

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
