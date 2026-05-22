import unittest
import json
import os
import sys

# Ensure the module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../substrates/400-499_advanced/substrato_signal_integrity_role')))

from substrato_signal_integrity_role import SubstratoSignalIntegrityRole

class TestSubstratoSignalIntegrityRole(unittest.TestCase):
    def test_canonize(self):
        substrate = SubstratoSignalIntegrityRole()
        path = substrate.canonize()
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data['Title'], "Signal Integrity Engineer")
        self.assertIn("PCB Stackup", data['Responsibilities'])
        self.assertEqual(data['Responsibilities']['PCB Stackup'], "Define PCB stackup, impedance profiles, and routing constraints in collaboration with layout engineers.")

        # Check no f-strings or non-ascii by simply reading raw bytes
        with open(path, 'rb') as f:
            raw_data = f.read()
            self.assertTrue(all(b < 128 for b in raw_data), "Non-ASCII characters found")

        os.remove(path)

if __name__ == '__main__':
    unittest.main()
