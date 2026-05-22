import unittest
import importlib.util
import os
import json

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class TestSubstratoPolyglotStack(unittest.TestCase):
    def test_canonize(self):
        path = "substrates/400-499_advanced/substrato_polyglot_stack/substrato_polyglot_stack.py"
        module = load_module_from_path("substrato_polyglot_stack", path)
        substrate = module.SubstratoPolyglotStack()

        # Test invariants
        self.assertEqual(substrate.phi_c, 0.994)
        self.assertEqual(substrate.principles, 15)
        self.assertEqual(substrate.languages, 10)

        out_path = substrate.canonize()
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["phi_c"], 0.994)
        self.assertEqual(data["principles_materialized"], 15)
        self.assertEqual(data["status"], "DELIVERED")

        # Verify no non-ASCII characters or f-strings in python source
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertNotIn("f\"", content)
            self.assertNotIn("f'", content)

        os.remove(out_path)

if __name__ == '__main__':
    unittest.main()
