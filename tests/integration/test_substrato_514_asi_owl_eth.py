import unittest
import os
import json
import tempfile
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../substrates/500-599_transcendence/substrato_514_asi_owl_eth/')))
from substrato_514_asi_owl_eth import SubstratoAsiOwlEth

class TestSubstratoAsiOwlEth(unittest.TestCase):
    def test_canonize_creates_valid_json(self):
        substrate = SubstratoAsiOwlEth()
        path = substrate.canonize()

        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["Title"], "SUBSTRATE 514-ASI.OWL.ETH: DESCENTRALIZED CONSTITUTION VERIFICATION")
        self.assertTrue("CID_Validity" in data)
        self.assertTrue("ENS_Validity" in data)
        self.assertTrue("Solidity_Analysis" in data)
        self.assertTrue("Phi_C_Calculation" in data)

        os.remove(path)

    def test_no_f_strings_or_non_ascii(self):
        source_file = os.path.join(os.path.dirname(__file__), '../../substrates/500-599_transcendence/substrato_514_asi_owl_eth/substrato_514_asi_owl_eth.py')

        with open(source_file, 'rb') as f:
            content = f.read()

        try:
            content.decode('ascii')
            is_ascii = True
        except UnicodeDecodeError:
            is_ascii = False

        self.assertTrue(is_ascii, "File contains non-ASCII characters")

        content_str = content.decode('ascii')
        self.assertFalse("f'" in content_str or 'f"' in content_str, "File appears to contain f-strings")

if __name__ == '__main__':
    unittest.main()
