import asyncio
import time
import hashlib
import unittest
from tri_operation_pipeline import TriOperationPipeline, TriOperationResult
from regional_expansion.custom_region_simulator import CustomRegionConfig, RegulatoryFramework
from firmware.phi_c_link_calculator import FirmwareLinkMetrics, LinkType
from production.top_secret_deploy import TOPSecretPayload, ClassificationLevel, PQCAlgorithm

class TestTriOperationPipeline(unittest.IsolatedAsyncioTestCase):
    async def test_tri_operation_pipeline(self):
        # 1. Configurar região
        region = CustomRegionConfig(
            region_id="ap-southeast-3",
            name="Asia Pacific SouthEast 3",
            location={"city": "Singapore", "country": "Singapore", "coordinates": (1.3521, 103.8198)},
            infrastructure_profile={"edge_compute": "high", "tf_qkd_backbone": "active"},
            regulatory_framework=RegulatoryFramework.PDPL
        )

        # 2. Configurar métricas de firmware
        link = FirmwareLinkMetrics(
            rssi_dbm=-45, snr_db=35, tx_power_dbm=20,
            latency_ms=5, jitter_ms=1, packet_loss_rate=0.0001,
            throughput_mbps=1000, encryption_type="AES-256-GCM",
            key_rotation_hours=1, integrity_checks_passed=10000, integrity_checks_total=10000,
            link_type=LinkType.ETHERNET_100G, channel_utilization=0.2, interference_level=0.01
        )

        # 3. Configurar payload
        payload = TOPSecretPayload(
            payload_id="SG_NODE_INIT_001",
            classification=ClassificationLevel.TOP_SECRET,
            content_hash=hashlib.sha3_512(b"NODE_KEYS").hexdigest(),
            metadata={"type": "initialization"},
            source_agency="ARKHE_CORE",
            destination_agency="SG_HUB",
            need_to_know_compartments=["ARKHE_OPS"],
            expiry_timestamp=time.time() + 3600,
            encryption_algorithm=PQCAlgorithm.KYBER_1024,
            signature_algorithm=PQCAlgorithm.DILITHIUM_5,
            public_key_fingerprint="sg_hub_pubkey_123"
        )

        pipeline = TriOperationPipeline(operator_id="TEST_ORCHESTRATOR")

        result = await pipeline.execute_pipeline(region, link, payload)

        self.assertIsInstance(result, TriOperationResult)
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.region_id, "ap-southeast-3")
        self.assertGreaterEqual(result.link_phi_c, 0.577553)
        self.assertIsNotNone(result.expansion_seal)
        self.assertIsNotNone(result.firmware_seal)
        self.assertIsNotNone(result.deploy_seal)
        self.assertIsNotNone(result.tri_operation_seal)

if __name__ == '__main__':
    unittest.main()
