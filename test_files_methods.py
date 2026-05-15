import sys
import unittest
import asyncio

class TestIntegrations(unittest.TestCase):
    def test_import_broadcast(self):
        try:
            from arkhe_tv.broadcast_guardian import ArkheTVGuardian, ContentValidation, SignalIntegrity
            guardian = ArkheTVGuardian()
            # test method without async
            res = asyncio.run(guardian.validate_physical_layer("test", {}))
            self.assertEqual(res.carrier_to_noise_db, 25.0)
            self.assertEqual(res.modulation_error_ratio_db, 30.0)
            res2 = asyncio.run(guardian.validate_content(b"video", b"audio", {}))
            self.assertEqual(res2.vvc_bitrate_efficiency, 0.12)
        except Exception as e:
            self.fail(f"broadcast_guardian validation failed: {e}")

    def test_import_ginga(self):
        try:
            from arkhe_tv.ginga_guardian import GingaSecurityWrapper
            wrapper = GingaSecurityWrapper()
            res = asyncio.run(wrapper.validate_ncl_app("test_app", "1"))
            self.assertTrue(res)
            res = asyncio.run(wrapper.validate_html5_app("test_app", "1"))
            self.assertTrue(res)
        except Exception as e:
            self.fail(f"ginga_guardian validation failed: {e}")

    def test_import_pqc(self):
        try:
            from crypto.pqc_crypto_adapter import PQCCryptoAdapter
            adapter = PQCCryptoAdapter()
            keypair = adapter.generate_keypair()
            self.assertIn("public_key", keypair)
        except Exception as e:
            self.fail(f"pqc_crypto_adapter import failed: {e}")

    def test_import_eal4(self):
        try:
            from compliance.eal4_certification_manager import EAL4CertificationManager
            mgr = EAL4CertificationManager()
            target = mgr.generate_security_target()
            self.assertEqual(target.product_name, "ARKHE Cathedral Kernel")
        except Exception as e:
            self.fail(f"eal4_certification_manager import failed: {e}")

    def test_import_siem(self):
        try:
            from integrations.siem_connector import SIEMConnector, SIEMConfig, SIEMPlatform
            cfg = SIEMConfig(platform=SIEMPlatform.SPLUNK, endpoint_url="http://test", api_token="test")
            connector = SIEMConnector(cfg)
            res = connector.health_check()
            self.assertIn("connected", res)
        except Exception as e:
            self.fail(f"siem_connector import failed: {e}")

if __name__ == '__main__':
    unittest.main()
