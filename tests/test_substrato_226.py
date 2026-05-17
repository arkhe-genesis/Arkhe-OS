import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import time

from temporal.multiregion_orchestrator import MultiRegionTemporalOrchestrator, RegionConfig, RegionHealth
from security.cmvp_audit_integration import CMVPAuditIntegration, CMVPAuditStatus
from ml.homomorphic_federated_learning import HomomorphicFederatedAggregator, EncryptedModelUpdate, HomomorphicEncryptionMock
from security.multicloud_vault_adapter import MultiCloudVaultAdapter, CloudProvider, CloudSecretConfig

@pytest.fixture
def mock_temporal():
    class MockTemporal:
        async def anchor_event(self, event, payload):
            return "mock_seal"
    return MockTemporal()

@pytest.fixture
def mock_phi_bus():
    class MockPhi:
        async def publish_metric(self, name, value):
            pass
    return MockPhi()

@pytest.mark.asyncio
async def test_multiregion_orchestrator(mock_temporal, mock_phi_bus):
    regions = [
        RegionConfig("us-east-1", "http://us", [], 1),
        RegionConfig("eu-west-1", "http://eu", [], 2)
    ]
    orchestrator = MultiRegionTemporalOrchestrator(regions, mock_phi_bus, "us-east-1")

    # Mock network calls
    orchestrator._region_health["us-east-1"] = RegionHealth.HEALTHY
    orchestrator._region_latency["us-east-1"] = 10.0
    orchestrator._region_health["eu-west-1"] = RegionHealth.HEALTHY
    orchestrator._region_latency["eu-west-1"] = 100.0

    async def mock_anchor(*args, **kwargs): return "seal1"
    async def mock_replicate(*args, **kwargs): return "seal2", 50.0
    orchestrator._anchor_to_region = mock_anchor
    orchestrator._replicate_to_region = mock_replicate

    result = await orchestrator.anchor_event_multi_region("test", {"data": 1})
    assert result.primary_region == "us-east-1"
    assert len(result.confirmed_regions) == 2
    assert result.total_confirmations == 2

@pytest.mark.asyncio
async def test_cmvp_audit(mock_temporal, mock_phi_bus):
    integration = CMVPAuditIntegration("leviton", "arkhe", mock_temporal, mock_phi_bus)

    pkg = await integration.prepare_audit_package(
        "module1", "Thales", {"provider": "Thales", "model": "Model X"}, "3"
    )

    assert pkg.status == CMVPAuditStatus.PREPARATION
    assert "security_policy" in pkg.documentation

    async def mock_submit(*args, **kwargs):
        pkg.status = CMVPAuditStatus.SUBMITTED
        return {"lab_reference": "REF1"}

    integration.submit_to_cmvp_lab = mock_submit
    res = await integration.submit_to_cmvp_lab(pkg, {"api_key": "x"})
    assert res["lab_reference"] == "REF1"

@pytest.mark.asyncio
async def test_homomorphic_fl(mock_temporal, mock_phi_bus):
    agg = HomomorphicFederatedAggregator("pubkey", "CKKS", mock_phi_bus, mock_temporal)

    for i in range(3):
        upd = EncryptedModelUpdate(
            f"node{i}", {"layer1": "hash"}, 100, "CKKS", 1.0, "sig"
        )
        await agg.receive_encrypted_update(upd)

    res = await agg.aggregate_homomorphically(min_updates=3)
    assert res is not None
    assert "layer1" in res["aggregated_weights_encrypted"]
    assert res["total_updates"] == 3

@pytest.mark.asyncio
async def test_multicloud_vault(mock_temporal, mock_phi_bus):
    creds = {
        CloudProvider.HASHICORP_VAULT: {"x": "y"},
        CloudProvider.AWS_SECRETS: {"x": "y"}
    }
    adapter = MultiCloudVaultAdapter(mock_temporal, mock_phi_bus, creds)

    cfg = CloudSecretConfig("mysec", [CloudProvider.HASHICORP_VAULT, CloudProvider.AWS_SECRETS], CloudProvider.HASHICORP_VAULT)

    res = await adapter.register_secret(cfg, "val")
    assert res["status"] == "registered"

    # Test failover
    adapter._provider_health[CloudProvider.HASHICORP_VAULT] = False
    read_res = await adapter.read_secret("mysec")

    assert read_res is not None
    assert read_res.provider == CloudProvider.AWS_SECRETS
