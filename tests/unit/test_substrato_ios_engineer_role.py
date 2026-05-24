import unittest
import os
import json
import importlib.util

class TestSubstratoIOSEngineerRole(unittest.TestCase):
    def test_canonize(self):
        spec = importlib.util.spec_from_file_location("substrato_ios_engineer_role", "substrates/400-499_advanced/substrato_ios_engineer_role/substrato_ios_engineer_role.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        substrate = module.SubstratoIOSEngineerRole()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as f:
            data = json.load(f)
        self.assertEqual(data["Title"], "iOS Engineer Role at Arkhe")
        os.remove(path)

if __name__ == '__main__':
    unittest.main()
