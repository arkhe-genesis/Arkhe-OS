import asyncio
import logging
import hashlib
import time
from typing import Dict, Any

from orchestration.delegated_orchestrator import AgentProposal, DelegatedOrchestrator, MultiOrchestratorConsensus
from security.delegated_hsm_signer import DelegatedHSMSigner
from security.hsm_production_integration import HSMProductionConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DelegatedSignatureSubstrate")

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

async def run_delegated_signature_pipeline():
    logger.info("🏛️  ARKHE Ω‑TEMP v∞.Ω — SUBSTRATO ∞: DELEGATED SIGNATURE")

    # 1. Setup TemporalChain e HSM
    temporal = MockTemporalChain()

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
    hsm_config = MockConfig()
    hsm_signer = DelegatedHSMSigner(hsm_config=hsm_config, temporal=temporal)

    # 2. Setup Consenso Multi-Orquestrador
    orchestrator_1 = DelegatedOrchestrator("orch_alpha")
    orchestrator_2 = DelegatedOrchestrator("orch_beta")
    orchestrator_3 = DelegatedOrchestrator("orch_gamma")
    consensus = MultiOrchestratorConsensus([orchestrator_1, orchestrator_2, orchestrator_3])

    # 3. Agente Zero Propõe (sem chave)
    # Criamos a proposta com os parâmetros definidos
    proposal = AgentProposal(
        agent_id="agent_zero_rust",
        operation="transfer",
        payload={"amount": 1000, "destination": "vault_x"},
        phi_c=0.98,
        nonce=hashlib.sha256(str(time.time()).encode()).hexdigest()
    )

    # Agente gera selo canônico antes de enviar
    proposal.canonical_seal = proposal.canonical_hash()

    logger.info(f"🔷 Agente Zero submeteu proposta: {proposal.canonical_seal}")

    # 4. Orquestrador Valida
    validation = await consensus.validate_consensus(proposal)

    if not validation.approved:
        logger.error(f"❌ Proposta rejeitada. Razão: {validation.reason}")
        return

    logger.info(f"🔷 Orquestradores aprovaram proposta. Selo Orquestrador: {validation.orchestrator_seal}")

    # 5. HSM Assina
    signature_result = await hsm_signer.sign_proposal(proposal, validation)

    if not signature_result["success"]:
        logger.error(f"❌ HSM falhou em assinar a proposta. Razão: {signature_result.get('error')}")
        return

    logger.info(f"🔷 HSM assinou com PQC ({signature_result['algorithm']}). Selo: {signature_result['signature']}")

    # 6. TemporalChain Ancora
    # Concatenação final
    concatenated = f"{proposal.canonical_hash()}:{validation.orchestrator_seal}:{signature_result['signature']}"
    event_hash = hashlib.sha3_256(concatenated.encode()).hexdigest()

    temporal_seal = await temporal.anchor_event(
        "delegated_signature_completed",
        {
            "proposal_hash": proposal.canonical_hash(),
            "agent_id": proposal.agent_id,
            "phi_c": proposal.phi_c,
            "orchestrator_seal": validation.orchestrator_seal,
            "pqc_signature": signature_result['signature'],
            "algorithm": signature_result['algorithm'],
            "timestamp": time.time(),
            "event_hash": event_hash
        }
    )

    logger.info(f"🔷 TemporalChain ancorou evento imutável. Selo: {temporal_seal}")
    logger.info("✅ DELEGATED_SIGNATURE: PROPOSE • VALIDATE • SIGN • ANCHOR COMPLETADO")

if __name__ == "__main__":
    asyncio.run(run_delegated_signature_pipeline())
