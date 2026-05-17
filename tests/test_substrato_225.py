import pytest
import asyncio
import time
from typing import Dict, List, Optional

from temporal.cluster_config import (
    ClusterConfig, ClusterNodeConfig, ClusterNodeRole, TemporalChainClusterClient
)
from security.fips140_3_compliance import (
    FIPS140_3ComplianceChecker, FIPS140_3SecurityLevel
)
from ml.federated_scale_orchestrator import (
    FederatedScaleOrchestrator, FederatedNode, AggregationTier
)
from security.vault_manager import (
    VaultSecretManager, SecretRotationPolicy
)

class MockTemporalChain:
    def __init__(self):
        self.events = []

    async def anchor_event(self, event_type: str, payload: Dict) -> str:
        self.events.append({"type": event_type, "payload": payload})
        return f"mock_seal_{len(self.events)}"

@pytest.mark.asyncio
async def test_temporalchain_cluster():
    config = ClusterConfig(
        cluster_id="test-cluster",
        nodes=[
            ClusterNodeConfig("n1", ClusterNodeRole.PRIMARY, "http://n1", "reg1"),
            ClusterNodeConfig("n2", ClusterNodeRole.VALIDATOR, "http://n2", "reg1"),
            ClusterNodeConfig("n3", ClusterNodeRole.VALIDATOR, "http://n3", "reg2"),
        ]
    )

    client = TemporalChainClusterClient(config)
    primary = await client.discover_primary()

    assert primary is not None
    assert primary in ["n1", "n2", "n3"]

    health = client.get_cluster_health()
    assert health["active_nodes"] == 3
    assert health["quorum_healthy"] is False  # 3 < min_nodes_for_consensus(4)

@pytest.mark.asyncio
async def test_fips_compliance():
    temporal = MockTemporalChain()
    checker = FIPS140_3ComplianceChecker("TestHSM", FIPS140_3SecurityLevel.LEVEL_3, temporal)

    # Teste de conformidade bem-sucedido
    valid_metadata = {
        "role_based_auth": True,
        "tamper_response": "zeroize",
        "firmware_selftest": True,
        "rng_algorithm": "CTR_DRBG",
        "side_channel_protections": ["constant_time", "masking"]
    }

    result = await checker.validate_operation("key_generation", valid_metadata)
    assert result["compliant"] is True

    # Verifica cache
    result2 = await checker.validate_operation("key_generation", valid_metadata)
    assert result2["cached"] is True

    # Teste de falha de conformidade
    invalid_metadata = valid_metadata.copy()
    invalid_metadata["tamper_response"] = "log_only"

    result_invalid = await checker.validate_operation("key_generation", invalid_metadata)
    assert result_invalid["compliant"] is False

@pytest.mark.asyncio
async def test_federated_scale():
    temporal = MockTemporalChain()
    orchestrator = FederatedScaleOrchestrator(None, None, temporal)

    # Registrar nós
    n1 = FederatedNode("n1", "reg1", {"compute": 0.8, "reliability": 0.9})
    n2 = FederatedNode("n2", "reg1", {"compute": 0.7, "reliability": 0.85})
    n3 = FederatedNode("n3", "reg2", {"compute": 0.9, "reliability": 0.95})

    await orchestrator.register_node(n1)
    await orchestrator.register_node(n2)
    await orchestrator.register_node(n3)

    selected = await orchestrator.select_nodes_for_round()
    assert len(selected) == 3

    updates = [
        {"node_id": "n1", "region": "reg1", "weights": {"w": 1.0}, "phi_c_contribution": 0.95},
        {"node_id": "n2", "region": "reg1", "weights": {"w": 2.0}, "phi_c_contribution": 0.90},
        {"node_id": "n3", "region": "reg2", "weights": {"w": 3.0}, "phi_c_contribution": 0.98},
    ]

    result = await orchestrator.execute_hierarchical_aggregation(updates, dp_epsilon=10.0)

    assert result.tier == AggregationTier.GLOBAL
    assert result.participating_nodes == 3
    assert result.phi_c_score > 0.9

    stats = orchestrator.get_scale_statistics()
    assert stats["total_registered"] == 3
    assert stats["rounds_completed"] == 1

@pytest.mark.asyncio
async def test_vault_integration():
    temporal = MockTemporalChain()

    async with VaultSecretManager("http://mock-vault", temporal_chain=temporal) as vault:
        policy = SecretRotationPolicy("test/secret", 30)
        vault.register_rotation_policy(policy)

        success = await vault.write_secret("test/secret", {"value": "secret123"})
        assert success is True

        secret = await vault.read_secret("test/secret")
        assert secret is not None

        # Testar acesso registrado
        summary = vault.get_audit_summary()
        assert summary["total_accesses"] > 0
