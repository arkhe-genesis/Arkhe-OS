import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import time

from arkhe_os.integration.ping_to_mrc_adapter import PingToMRCProbeAdapter
from arkhe_os.coherence.path_coherence_estimator import AdaptiveBaselineEstimator
from arkhe_os.parser.frontends.ping_frontend_async import PingResult
from arkhe_os.audit.ping_audit_ledger import PingAuditLedger

@pytest.mark.asyncio
async def test_mrc_adapter_low_coherence_triggers_probe():
    mock_mrc = AsyncMock()
    estimator = AdaptiveBaselineEstimator()
    adapter = PingToMRCProbeAdapter(mrc_controller=mock_mrc, coherence_estimator=estimator, trigger_threshold=0.6)

    # Create a result with high loss, resulting in low coherence
    bad_result = PingResult(
        target="target.local",
        rtt_avg_ms=200.0,
        rtt_min_ms=180.0,
        rtt_max_ms=250.0,
        jitter_ms=20.0,
        loss_rate=0.8, # 80% loss
        ttl=64,
        coherence=0.0, # placeholder, will be overwritten by adapter
        timestamp=time.time()
    )

    await adapter.sync_path_health("target.local", bad_result)

    # Verify MRC was updated
    mock_mrc.update_path_coherence.assert_called_once()

    args, kwargs = mock_mrc.update_path_coherence.call_args
    assert kwargs["destination"] == "target.local"
    assert kwargs["coherence_score"] < 0.6  # Given high loss, score should be low
    assert kwargs["metrics"]["loss"] == 0.8

    # Verify active probe was triggered due to low coherence
    mock_mrc.trigger_active_probe.assert_called_once_with("target.local", reason="low_coherence")

def test_audit_ledger_integrity_hash():
    ledger = PingAuditLedger()

    result = PingResult(
        target="10.0.0.1",
        rtt_avg_ms=45.0,
        rtt_min_ms=40.0,
        rtt_max_ms=50.0,
        jitter_ms=5.0,
        loss_rate=0.0,
        ttl=64,
        coherence=0.95,
        timestamp=1000000.0 # Fixed timestamp for deterministic hash check
    )

    entry = ledger.log_session(result, "session_42")

    assert len(ledger.ledger) == 1
    assert entry["session_id"] == "session_42"
    assert entry["proof_hash"] is not None

    # Verify hash manually
    import hashlib
    expected_data = f"session_42:10.0.0.1:45.0:0.0:5.0:1000000.0:{ledger.node_key}"
    expected_hash = hashlib.sha256(expected_data.encode('utf-8')).hexdigest()

    assert entry["proof_hash"] == expected_hash