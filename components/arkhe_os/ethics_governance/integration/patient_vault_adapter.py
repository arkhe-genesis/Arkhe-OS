"""
Adapter para integração com Patient Vault (Substrato 287).
Permite que verificações éticas respeitem consentimentos granulares dos pacientes.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Assuming EthicsProof and EthicsZKProver can be imported or typed as Any to avoid circular dependencies
@dataclass
class EthicalConsent:
    """Consentimento ético granular do paciente."""
    consent_id: str
    patient_id_hash: str
    # Escopos de uso ético permitidos
    allowed_purposes: List[str]  # ["research", "clinical_decision", "model_training"]
    # Restrições de fairness aplicáveis
    fairness_requirements: Dict[str, float]  # {"demographic_parity_alpha": 0.05, ...}
    # Preferências de explicabilidade
    explainability_level: str  # "none", "local", "global", "causal"
    # Consentimento para uso em proofs ZK
    allow_zk_verification: bool
    # Timestamp e expiração
    granted_at: str
    expires_at: Optional[str]

    def is_valid_for_purpose(self, purpose: str) -> bool:
        """Verifica se propósito é permitido pelo consentimento."""
        return purpose in self.allowed_purposes

    def get_fairness_params(self) -> Dict[str, float]:
        """Retorna parâmetros de fairness do consentimento."""
        return self.fairness_requirements.copy()

class PatientVaultEthicsAdapter:
    """Adapter para consultar consentimentos éticos do Patient Vault."""

    def __init__(self, vault_endpoint: str, zk_proof_verifier: Any):
        self.vault_endpoint = vault_endpoint
        self.zk_verifier = zk_proof_verifier

    def get_ethical_consents(self, patient_id_hash: str,
                           requested_purpose: str) -> List[EthicalConsent]:
        """
        Recupera consentimentos éticos válidos para um paciente e propósito.

        Usa ZK-proofs para verificar validade do consentimento sem revelar identidade.
        """
        # Em produção: chamada API para Patient Vault com ZK-proof de autorização
        # Aqui: simulação de resposta
        return [
            EthicalConsent(
                consent_id="consent_demo_001",
                patient_id_hash=patient_id_hash,
                allowed_purposes=["research", "clinical_decision"],
                fairness_requirements={
                    "demographic_parity_alpha": 0.05,
                    "equal_opportunity_alpha": 0.05,
                },
                explainability_level="causal",
                allow_zk_verification=True,
                granted_at="2026-01-01T00:00:00Z",
                expires_at="2027-01-01T00:00:00Z",
            )
        ]

    def verify_ethical_usage(self, model_id: str,
                           patient_consents: List[EthicalConsent],
                           ethics_proof: Any) -> bool:
        """
        Verifica se uso do modelo para pacientes com dados consentimentos é ético.

        Combina:
        1. Validação de consentimentos (via ZK-proof do Patient Vault)
        2. Verificação do ethics proof do modelo
        3. Checagem de que requisitos de fairness dos consentimentos são atendidos
        """
        # 1. Verificar ethics proof do modelo
        if not self.zk_verifier.verify_proof(ethics_proof, ethics_proof.public_inputs):
            return False

        # 2. Extrair fairness params do proof (assumindo que estão nos public_inputs)
        proof_fairness = ethics_proof.public_inputs.get("fairness_params", {})

        # 3. Verificar se proof satisfaz requisitos de todos os consentimentos
        for consent in patient_consents:
            required_fairness = consent.get_fairness_params()
            for key, required_value in required_fairness.items():
                proof_value = proof_fairness.get(key)
                if proof_value is None:
                    # In our example, the test public inputs has the metrics directly. Let's look for them if not in fairness_params
                    # Try direct match
                    proof_value = ethics_proof.public_inputs.get(key)
                    # Try mapping from requirements to metrics format
                    if proof_value is None and key.endswith("_alpha"):
                        metric_key = key.replace("_alpha", "_diff")
                        proof_value = ethics_proof.public_inputs.get(metric_key)

                    if proof_value is None:
                        return False  # Proof não cobre este requisito
                if proof_value > required_value:
                    return False  # Proof não atende threshold requerido

        return True
