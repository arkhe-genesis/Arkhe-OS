import pytest
import asyncio
import hashlib
import time
from typing import Dict, Any

from orchestration.delegated_orchestrator import AgentProposal, DelegatedOrchestrator, MultiOrchestratorConsensus
from security.delegated_hsm_signer import DelegatedHSMSigner
from security.hsm_production_integration import HSMProductionConfig

class MockTemporalChain:
    def __init__(self):
        self.ledger = []

    async def anchor_event(self, event_type: str, payload: Dict[str, Any]) -> str:
        event_json = str(payload).encode()
        event_hash = hashlib.sha3_256(event_json).hexdigest()
        chain_signature = hashlib.sha3_256(event_hash.encode() + b"temporal_chain_key").hexdigest()

        self.ledger.append({
            "hash": event_hash,
            "signature": chain_signature,
            "payload": payload,
        })

        return chain_signature

@pytest.fixture
def temporal():
    return MockTemporalChain()

@pytest.fixture
def hsm_config():
    class MockConfig:
        provider = "thales_ncipher"
        pkcs11_library = "/opt/nfast/toolkits/pkcs11/libcknfast.so"
        slot_id = 1
        token_label = "arkhe_prod"
        key_label = "pqc_delegated_key"
        pqc_algorithm = "dilithium3"
        pin_vault_path = "secret/hsm/pin"
        rotation_policy_days = 90
        audit_all_operations = True
        fallback_classic = True
    return MockConfig()

@pytest.mark.asyncio
async def test_delegated_signature_full_flow(temporal, hsm_config):
    # 1. Setup
    hsm_signer = DelegatedHSMSigner(hsm_config=hsm_config, temporal=temporal)

    o1 = DelegatedOrchestrator("orch_1")
    o2 = DelegatedOrchestrator("orch_2")
    o3 = DelegatedOrchestrator("orch_3")
    consensus = MultiOrchestratorConsensus([o1, o2, o3])

    # 2. Agente propõe
    proposal = AgentProposal(
        agent_id="agent_zero",
        operation="transfer",
        payload={"amount": 1000},
        phi_c=0.98,
        nonce=hashlib.sha256(str(time.time()).encode()).hexdigest()
    )
    proposal.canonical_seal = proposal.canonical_hash()

    # 3. Validação do Orquestrador
    validation = await consensus.validate_consensus(proposal)
    assert validation.approved is True
    assert validation.orchestrator_seal is not None

    # 4. Assinatura PQC com HSM
    sig_result = await hsm_signer.sign_proposal(proposal, validation)
    assert sig_result["success"] is True
    assert sig_result["algorithm"] == "CKM_DILITHIUM3"
    assert sig_result["signature"] is not None
    assert sig_result["fips_compliant"] is True

    # 5. Ancoragem no TemporalChain
    concatenated = f"{proposal.canonical_hash()}:{validation.orchestrator_seal}:{sig_result['signature']}"
    event_hash = hashlib.sha3_256(concatenated.encode()).hexdigest()

    temporal_seal = await temporal.anchor_event(
        "delegated_signature_completed",
        {
            "proposal_hash": proposal.canonical_hash(),
            "agent_id": proposal.agent_id,
            "phi_c": proposal.phi_c,
            "orchestrator_seal": validation.orchestrator_seal,
            "pqc_signature": sig_result['signature'],
            "algorithm": sig_result['algorithm'],
            "timestamp": time.time(),
            "event_hash": event_hash
        }
    )

    assert temporal_seal is not None
    assert len(temporal.ledger) > 0

@pytest.mark.asyncio
async def test_delegated_orchestrator_rejection(temporal, hsm_config):
    o1 = DelegatedOrchestrator("orch_1")

    # Proposta com phi_c baixo
    proposal = AgentProposal(
        agent_id="agent_zero",
        operation="transfer",
        payload={"amount": 1000},
        phi_c=0.90, # Abaixo do threshold de 0.95
        nonce="nonce123"
    )
    proposal.canonical_seal = proposal.canonical_hash()

    validation = await o1.validate_proposal(proposal)
    assert validation.approved is False
    assert validation.rejected is True
    assert validation.reason == "phi_c_below_threshold"

    # HSM deve recusar
    hsm_signer = DelegatedHSMSigner(hsm_config=hsm_config, temporal=temporal)
    sig_result = await hsm_signer.sign_proposal(proposal, validation)
    assert sig_result["success"] is False
    assert sig_result["error"] == "invalid_proposal"

@pytest.mark.asyncio
async def test_replay_attack_prevention():
    o1 = DelegatedOrchestrator("orch_1")

    nonce = "reusable_nonce_123"

    proposal = AgentProposal(
        agent_id="agent_zero",
        operation="transfer",
        payload={"amount": 1000},
        phi_c=0.98,
        nonce=nonce
    )
    proposal.canonical_seal = proposal.canonical_hash()

    # Primeira vez deve funcionar
    val1 = await o1.validate_proposal(proposal)
    assert val1.approved is True

    # Segunda vez deve ser rejeitado
    val2 = await o1.validate_proposal(proposal)
    assert val2.approved is False
    assert val2.reason == "replay_detected"
