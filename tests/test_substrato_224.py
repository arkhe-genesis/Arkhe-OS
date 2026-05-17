import pytest
import asyncio
import json
import torch
import torch.nn as nn
import hashlib
from temporal.production_client import TemporalChainProductionClient, TemporalChainConfig
from security.hsm_production_integration import HSMProductionPQCSigner, HSMProductionConfig
from ml.federated_delta_mem_production import FederatedDeltaMemProduction, FederatedTrainingConfig, LocalModelUpdate

class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(384, 64)

class DummyPredictor:
    def __init__(self):
        self.model = DummyModel()

@pytest.mark.asyncio
async def test_temporal_chain_client():
    config = TemporalChainConfig(
        endpoint="https://mock.temporal.arkhe.os/v1",
        client_cert_path="dummy.crt",
        client_key_path="dummy.key",
        ca_cert_path="dummy_ca.crt"
    )

    async with TemporalChainProductionClient(config) as client:
        result = await client.anchor_event("test_event", {"data": "test_payload"})
        assert result["status"] == "anchored"
        assert "seal" in result

        is_valid = await client.verify_seal(result["seal"], result["event_id"])
        assert is_valid is True

@pytest.mark.asyncio
async def test_hsm_production_integration():
    config = HSMProductionConfig(
        provider="simulated",
        pkcs11_library="dummy.so",
        slot_id=1,
        token_label="ARKHE_TEST",
        key_label="test_key",
        pqc_algorithm="CRYSTALS-Dilithium3",
        pin_vault_path="dummy/path"
    )

    async with HSMProductionPQCSigner(config) as signer:
        data = b"test data for signing"
        result = await signer.sign_data(data)

        assert result["success"] is True
        assert result["algorithm"] == "CRYSTALS-Dilithium3"
        assert "signature_hex" in result

        # Testar verificação no modo simulado
        is_valid = await signer.verify_signature(data, result["signature_hex"])
        assert is_valid is True

        # Testar rotação simulada
        rot_result = await signer.rotate_key()
        assert "new_key" in rot_result

@pytest.mark.asyncio
async def test_federated_delta_mem():
    config = FederatedTrainingConfig(node_id="node-test-1")
    predictor = DummyPredictor()

    federated = FederatedDeltaMemProduction(
        config=config,
        local_predictor=predictor
    )

    experiences = [{"sensitivity_score": 0.8, "success": 1.0}]
    update = await federated.prepare_local_update(experiences)

    assert update.node_id == "node-test-1"
    assert update.training_samples == 1
    assert update.dp_noise_epsilon < 5.0 # Due to high sensitivity

    # Simular updates de multiplos nós

    node2_id = "node-test-2"
    # Generate the proper mock PQC signature for node 2
    expected_sig = hashlib.sha3_256(
        update.model_weights + node2_id.encode()
    ).hexdigest()

    update2 = LocalModelUpdate(
        node_id=node2_id,
        model_weights=update.model_weights,
        training_samples=1,
        local_loss=0.05,
        phi_c_contribution=0.98,
        dp_noise_epsilon=2.5,
        timestamp=1000.0,
        pqc_signature=expected_sig
    )

    result = await federated.aggregate_updates([update, update2])
    assert result["status"] == "success"
    assert result["valid_updates"] == 2

    stats = federated.get_federation_statistics()
    assert stats["rounds_completed"] == 1
