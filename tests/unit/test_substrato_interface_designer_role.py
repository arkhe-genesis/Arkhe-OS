import unittest
import os
import json
from unittest.mock import patch

# We need to import the substrate we just created
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../substrates/400-499_advanced/substrato_interface_designer_role'))

from substrato_interface_designer_role import SubstratoInterfaceDesignerRole

class TestSubstratoInterfaceDesignerRole(unittest.TestCase):
    def test_canonize(self):
        substrate = SubstratoInterfaceDesignerRole()
        path = substrate.canonize()

        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertIn("Role", data)
        self.assertEqual(data["Role"], "Interface Designer")
        self.assertIn("Introduction", data)
        self.assertIn("Responsibilities", data)
        self.assertIn("Requirements", data)

        # Check invariants
        with open(os.path.join(os.path.dirname(__file__), '../../substrates/400-499_advanced/substrato_interface_designer_role/substrato_interface_designer_role.py'), 'r') as f:
            content = f.read()
            self.assertNotIn("f'", content)
            self.assertNotIn('f"', content)

            # Simple check for non-ascii characters
            self.assertTrue(all(ord(c) < 128 for c in content), "Non-ASCII character found in file")

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
