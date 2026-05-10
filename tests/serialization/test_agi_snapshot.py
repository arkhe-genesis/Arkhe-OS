import sys
import unittest
import os
import unittest.mock

sys.path.append('arkhe-omega-temp/arkhe/substrate_6041_v3')

class TestAGISnapshot(unittest.TestCase):
    def test_agi_snapshot_serialization(self):
        try:
            # We mock cryptography to avoid env constraints since it requires it for AES-GCM
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            sys.modules['cryptography'] = unittest.mock.MagicMock()
            sys.modules['cryptography.hazmat'] = unittest.mock.MagicMock()
            sys.modules['cryptography.hazmat.primitives'] = unittest.mock.MagicMock()
            sys.modules['cryptography.hazmat.primitives.ciphers'] = unittest.mock.MagicMock()

            class MockAESGCM:
                def __init__(self, key):
                    pass
                @classmethod
                def generate_key(cls, bit_length):
                    return os.urandom(bit_length // 8)
                def encrypt(self, nonce, data, associated_data):
                    return data

            mock_aead = unittest.mock.MagicMock()
            mock_aead.AESGCM = MockAESGCM
            sys.modules['cryptography.hazmat.primitives.ciphers.aead'] = mock_aead

        try:
            from agi_packager import AGIPackage

            pkg = AGIPackage(name="snapshot-test", version="1.0.0", author="TEST-AUTHOR")
            pkg.add_artifact("main.py", b"print('hello snapshot')")

            serialized = pkg.build(sgx_enabled=False, sev_enabled=False)

            self.assertTrue(serialized.startswith(b'AGI\x04'))
            self.assertGreater(len(serialized), 100)
            self.assertIsInstance(serialized, bytes)

        except ImportError as e:
            self.fail(f"Could not import AGIPackage: {e}")

if __name__ == '__main__':
    unittest.main()
