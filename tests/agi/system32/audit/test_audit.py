#!/usr/bin/env python3
import asyncio
import time
from pathlib import Path
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add agi/system32 to path to import audit properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../agi/system32")))

from audit.ledger import AuditEvent, MerkleCRDTLedger
from audit.proof_generator import CoherenceProofGenerator, CoherenceProof
from audit.rekor_publisher import RekorPublisher
from audit.verifier import IndependentVerifier
from audit.deviation_tracker import DeviationTracker

class MockDHT:
    async def store(self, key, value):
        pass

class TestAuditProtocol(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.test_artifact_path = Path("test_artifact.agi")
        self.test_artifact_path.write_bytes(b"mock_agi_content")
        self.test_key_path = Path("test_key.pem")
        self.test_key_path.write_text("mock_key")
        self.dht = MockDHT()

    def tearDown(self):
        if self.test_artifact_path.exists():
            self.test_artifact_path.unlink()
        if self.test_key_path.exists():
            self.test_key_path.unlink()

    @patch('audit.ledger.falcon')
    @patch('audit.ledger.merkle_tree')
    async def test_ledger(self, mock_merkle_tree, mock_falcon):
        mock_falcon.verify.return_value = True
        mock_merkle_tree.compute_root.return_value = "mock_root"

        ledger = MerkleCRDTLedger("node_seal_1", self.dht)
        event = AuditEvent(
            event_id="evt_1",
            event_type="artifact_execution",
            timestamp=time.time(),
            actor_seal="node_seal_1",
            payload_hash="mock_payload_hash",
            coherence_score=0.9,
            signature="mock_signature",
            metadata={}
        )

        result = ledger.insert_event(event)
        self.assertTrue(result)
        self.assertEqual(len(ledger.local_events), 1)

    @patch('audit.proof_generator.falcon')
    def test_proof_generator(self, mock_falcon):
        mock_falcon.sign.return_value = "mock_falcon_signature"
        mock_falcon.load_key.return_value = "mock_key"

        generator = CoherenceProofGenerator("node_seal_1", self.test_key_path)
        proof = generator.generate_proof(
            self.test_artifact_path,
            {"stages": {"loading": {"coherence": 0.95}, "initialization": {"coherence": 0.95}, "execution": {"coherence": 0.95}, "finalization": {"coherence": 0.95}}},
            {"enable_zk_audit": True}
        )

        self.assertGreater(proof.overall_coherence, 0.9)
        self.assertIsNotNone(proof.zk_proof)
        self.assertEqual(proof.signature, "mock_falcon_signature")

    def test_rekor_publisher(self):
        # We can test with mock_requests=True on the publisher directly
        publisher = RekorPublisher("https://mock_rekor", mock_requests=True)

        mock_proof = MagicMock()
        mock_proof.artifact_hash = "hash123"
        mock_proof.artifact_seal = "seal123"
        mock_proof.overall_coherence = 0.9
        mock_proof.signature = "sig123"
        mock_proof.to_dict.return_value = {}

        entry = publisher.publish_proof(mock_proof, {"version": "1.0"})
        self.assertIsNotNone(entry)
        self.assertEqual(entry.rekor_uuid, "mock_uuid_123")

    @patch('audit.verifier.falcon')
    async def test_verifier(self, mock_falcon):
        mock_falcon.verify.return_value = True

        publisher = RekorPublisher("https://mock_rekor", mock_requests=True)
        verifier = IndependentVerifier(self.dht, publisher)

        # Override canonical seals to include our test
        verifier.canonical_seals["test_artifact"] = "test"

        import hashlib
        artifact_hash = hashlib.sha3_256(self.test_artifact_path.read_bytes()).hexdigest()

        proof = CoherenceProof(
            artifact_hash=artifact_hash,
            artifact_seal="test_artifact",
            execution_timestamp=time.time(),
            coherence_by_stage={},
            overall_coherence=0.95,
            config_hash="confighash",
            signature="mock_sig",
            zk_proof=None
        )

        mock_entry = MagicMock()
        mock_entry.rekor_uuid = "uuid"
        mock_entry.inclusion_proof = {"root": "hash"}
        mock_entry.artifact_hash = artifact_hash

        result = await verifier.verify_artifact(self.test_artifact_path, proof, mock_entry)
        self.assertTrue(result.is_trusted())

    def test_deviation_tracker(self):
        canonical_config = {"min_coherence": 0.7, "version": "1.0"}
        tracker = DeviationTracker(canonical_config)

        alert = tracker.check_execution("seal_1", {"version": "2.0"}, 0.5)
        self.assertIsNotNone(alert)
        self.assertIn(alert.severity, ["critical", "high", "medium"])

if __name__ == "__main__":
    unittest.main()
