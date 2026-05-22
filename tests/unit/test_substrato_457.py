import unittest
import importlib.util
import os
import json

class TestSubstrato457Integrate(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "substrato_457_integrate",
            "substrates/400-499_advanced/substrato_457_integrate/substrato_457_integrate.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_adaptive_integration(self):
        integrator = self.module.AdaptiveIntegration()
        self.assertEqual(integrator.select_layer("control"), "455-POLAR")
        self.assertEqual(integrator.select_layer("qubit"), "453-QUANTUM")

        result = integrator.integrate("0101", "data")
        self.assertEqual(result["layer"], "456-TURBO")

        with self.assertRaises(ValueError):
            integrator.integrate("0101", "invalid_channel")

    def test_canonize(self):
        substrate = self.module.Substrato457Integrate()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as f:
            data = json.load(f)
        self.assertIn("SEAL_457_INTEGRATE", data)
        os.remove(path)

if __name__ == '__main__':
    unittest.main()
