import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

from arkhe.core.cross_platform.unified_runtime import (
    UnifiedArkheRuntime,
    TargetPlatform,
    SyncMode
)

from arkhe.core.cross_platform.phi_c_sync_protocol import (
    PhiCSyncProtocol,
    ConflictResolutionStrategy,
    SyncConflict
)

@pytest.fixture
def mock_phi_c_monitor():
    monitor = MagicMock()
    monitor.temporal_chain = AsyncMock()
    monitor.temporal_chain.anchor_event.return_value = "mocked_anchor_hash"
    monitor.get_current_coherence.return_value = 0.99
    return monitor

@pytest.mark.asyncio
async def test_unified_runtime_execution(mock_phi_c_monitor):
    # Test that the runtime can execute operations using its platform adapter
    # We force Linux platform to avoid platform dependency
    runtime = UnifiedArkheRuntime(platform=TargetPlatform.LINUX, sync_mode=SyncMode.OFFLINE_FIRST, phi_c_monitor=mock_phi_c_monitor)

    # file_access
    result = await runtime.execute_operation("file_access", {"path": "/tmp/arkhe_test"})
    assert result["success"] is True
    assert "temporal_anchor" in result

    # quantum_compute
    result = await runtime.execute_operation("quantum_compute", {})
    assert result["success"] is True
    assert result["backend_used"] == "qiskit_aer_simulator"

    await runtime.shutdown()


@pytest.mark.asyncio
async def test_phi_c_sync_protocol_phi_c_weighted():
    # Test conflict resolution strategy: PHI_C_WEIGHTED
    def mock_provider():
        return 0.98 # local phi_c

    temporal_chain = AsyncMock()

    protocol = PhiCSyncProtocol(
        local_phi_c_provider=mock_provider,
        temporal_chain=temporal_chain,
        strategy=ConflictResolutionStrategy.PHI_C_WEIGHTED
    )

    # Test resolving a conflict where local has higher phi_c and is newer
    now = time.time()

    local_state = {
        "config_value": 42,
        "_timestamp": now
    }

    remote_state = {
        "config_value": 100,
        "_remote_phi_c": 0.96, # remote is lower
        "_timestamp": now - 10 # older
    }

    merged, pending = await protocol.resolve_conflicts(local_state, remote_state, ["config_value"])

    assert len(pending) == 0
    assert merged["config_value"] == 42
    assert merged["config_value_resolved_by"] == "PHI_C_WEIGHTED"

@pytest.mark.asyncio
async def test_phi_c_sync_protocol_ambiguous_conflict():
    # Test conflict resolution strategy: PHI_C_WEIGHTED where weights are too close
    def mock_provider():
        return 0.97 # local phi_c

    temporal_chain = AsyncMock()

    protocol = PhiCSyncProtocol(
        local_phi_c_provider=mock_provider,
        temporal_chain=temporal_chain,
        strategy=ConflictResolutionStrategy.PHI_C_WEIGHTED
    )

    now = time.time()

    local_state = {
        "config_value": "alpha",
        "_timestamp": now
    }

    remote_state = {
        "config_value": "beta",
        "_remote_phi_c": 0.971, # remote is very close
        "_timestamp": now # same timestamp
    }

    merged, pending = await protocol.resolve_conflicts(local_state, remote_state, ["config_value"])

    # Should not be resolved automatically because difference is less than EPSILON (0.02)
    assert len(pending) == 1
    assert pending[0].key == "config_value"
    assert "config_value_resolved_by" not in merged

@pytest.mark.asyncio
async def test_phi_c_sync_protocol_temporal_latest():
    # Test conflict resolution strategy: TEMPORAL_LATEST
    def mock_provider():
        return 0.99

    temporal_chain = AsyncMock()

    protocol = PhiCSyncProtocol(
        local_phi_c_provider=mock_provider,
        temporal_chain=temporal_chain,
        strategy=ConflictResolutionStrategy.TEMPORAL_LATEST
    )

    now = time.time()

    local_state = {
        "status": "idle",
        "_timestamp": now - 5 # older
    }

    remote_state = {
        "status": "processing",
        "_remote_phi_c": 0.80, # low phi_c, but strategy is temporal
        "_timestamp": now # newer
    }

    merged, pending = await protocol.resolve_conflicts(local_state, remote_state, ["status"])

    assert len(pending) == 0
    assert merged["status"] == "processing"
    assert merged["status_resolved_by"] == "TEMPORAL_LATEST"
