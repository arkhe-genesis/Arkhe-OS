import pytest
from arkhe_os.healing.auto_healing import DynamicRebalancer, EmergencyRollbackOrchestrator

@pytest.mark.asyncio
async def test_dynamic_rebalancer():
    rebalancer = DynamicRebalancer()
    assert len(rebalancer.active_regions) == 3
    assert rebalancer.quorum_size == 3

    success = rebalancer.rebalance("ap-south-1")
    assert success is True
    assert len(rebalancer.active_regions) == 2
    assert rebalancer.quorum_size == 2
    assert "shard-05" in rebalancer.shards["us-east-1"]
    assert "shard-06" in rebalancer.shards["eu-central-1"]

@pytest.mark.asyncio
async def test_emergency_rollback_c01():
    rebalancer = DynamicRebalancer()
    orchestrator = EmergencyRollbackOrchestrator(rebalancer)

    omega, p99 = await orchestrator.simulate_c01_eclipse_da_torre()
    assert omega > 0.85
    assert p99 < 5.0
    assert len(orchestrator.rollback_log) == 1
    assert orchestrator.rollback_log[0]["severity"] == "REGION_ISOLATE"
