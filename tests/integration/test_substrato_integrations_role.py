import unittest
import os
import json
import tempfile
import sys

# Add the new substrate path so we can import it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../substrates/400-499_advanced/substrato_integrations_role/')))
from substrato_integrations_role import SubstratoIntegrationsRole

class TestSubstratoIntegrationsRole(unittest.TestCase):
    def test_canonize_creates_valid_json(self):
        substrate = SubstratoIntegrationsRole()
        path = substrate.canonize()

        # Verify the file was created
        self.assertTrue(os.path.exists(path))

        # Verify the content is valid JSON
        with open(path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["Title"], "Integrations Engineer Role")
        self.assertTrue("Description" in data)
        self.assertTrue("Responsibilities" in data)
        self.assertTrue("Requirements" in data)
        self.assertTrue("Bonus_Qualifications" in data)

        # Cleanup
        os.remove(path)

    def test_no_f_strings_or_non_ascii(self):
        source_file = os.path.join(os.path.dirname(__file__), '../../substrates/400-499_advanced/substrato_integrations_role/substrato_integrations_role.py')

        with open(source_file, 'rb') as f:
            content = f.read()

        # Verify it's valid ASCII
        try:
            content.decode('ascii')
            is_ascii = True
        except UnicodeDecodeError:
            is_ascii = False

        self.assertTrue(is_ascii, "File contains non-ASCII characters")

        # Basic check for f-strings
        content_str = content.decode('ascii')
        self.assertFalse("f'" in content_str or 'f"' in content_str, "File appears to contain f-strings")

if __name__ == '__main__':
    unittest.main()
