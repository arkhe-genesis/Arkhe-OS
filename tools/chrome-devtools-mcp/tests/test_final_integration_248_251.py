import pytest
import asyncio
import numpy as np
import tempfile
import os

from arkhe_os.crypto.fhe.nostr_fhe_engine import NostrFHEEngine, NostrEventComponents
from arkhe_os.metaconsciousness.network_coherence_synchronizer import NetworkCoherenceSynchronizer, RunnerCoherenceState
from arkhe_os.audit import FinalReleaseAuditLedger

@pytest.mark.asyncio
async def test_nostr_fhe_engine():
    engine = NostrFHEEngine(security_level=128)

    event = NostrEventComponents(
        pr_content="sensitive data that needs encryption",
        coherence_report={"omega": 0.95, "phi": 1.618},
        signature_data=b'secure_signature',
        public_meta={"type": "test_event"}
    )

    encrypted_dict = engine.encrypt_event(event, event_id="test_1")

    assert 'coherence_report' in encrypted_dict
    assert 'signature_data' in encrypted_dict
    assert 'pr_content' in encrypted_dict

@pytest.mark.asyncio
async def test_network_coherence_synchronizer():
    sync = NetworkCoherenceSynchronizer(
        local_npub="npub1test...",
        local_nsec="nsec1test...",
        relays=["wss://relay.test.io"]
    )

    assert sync.local_state.runner_id == "local"
    assert sync.local_state.reputation_score == 1.0
    assert len(sync.local_state.coherence_vector) == 256

    # Simulate network sync
    other_state = RunnerCoherenceState(
        runner_id="runner_2",
        npub="npub2...",
        coherence_vector=np.random.randn(256) / np.sqrt(256),
        last_sync_time=0,
        sync_phase=0.5,
        reputation_score=0.9
    )

    sync.known_runners["runner_2"] = other_state

    phase_adj = sync.compute_phase_locking(other_state)
    assert isinstance(phase_adj, float)

    await sync.synchronize_with_network()
    assert sync.sync_count == 1

def test_final_release_audit_ledger():
    ledger = FinalReleaseAuditLedger(
        release_version="test-1.0.0",
        canonical_seal="seal123"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "audit.json")
        report = ledger.export_full_audit(output_path)

        assert report["release_version"] == "test-1.0.0"
        assert report["canonical_seal"] == "seal123"
        assert os.path.exists(output_path)
