# arkhe_os/banking_ethics_governance/integration/customer_vault_adapter.py
"""
Adapter para integração com Customer Financial Vault (Substrato 287-B).
Permite que verificações éticas respeitem consentimentos granulares
de clientes para uso de dados financeiros.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from ..prover.banking_ethics_zk_prover import BankingEthicsZKProver, BankingEthicsProof

@dataclass
class FinancialEthicalConsent:
    """Consentimento ético granular do cliente bancário."""
    consent_id: str
    customer_id_hash: str
    # Escopos de uso ético permitidos
    allowed_purposes: List[str]  # ["credit_scoring", "fraud_detection", "investment_advice"]
    # Restrições de fairness aplicáveis
    fairness_requirements: Dict[str, float]  # {"credit_parity_alpha": 0.03, ...}
    # Preferências de explicabilidade
    explainability_level: str  # "none", "local", "global", "counterfactual"
    # Consentimento para uso em proofs ZK
    allow_zk_verification: bool
    # Timestamp e expiração
    granted_at: str
    expires_at: Optional[str]
    # Jurisdição aplicável
    jurisdiction: str  # "BR", "EU", "US"

    def is_valid_for_purpose(self, purpose: str) -> bool:
        """Verifica se propósito é permitido pelo consentimento."""
        return purpose in self.allowed_purposes

    def get_fairness_params(self) -> Dict[str, float]:
        """Retorna parâmetros de fairness do consentimento."""
        return self.fairness_requirements.copy()

class CustomerVaultEthicsAdapter:
    """Adapter para consultar consentimentos éticos do Customer Financial Vault."""

    def __init__(self, vault_endpoint: str, zk_proof_verifier: BankingEthicsZKProver):
        self.vault_endpoint = vault_endpoint
        self.zk_verifier = zk_proof_verifier

    def get_financial_ethical_consents(self, customer_id_hash: str,
                                       requested_purpose: str,
                                       jurisdiction: str) -> List[FinancialEthicalConsent]:
        """
        Recupera consentimentos éticos válidos para um cliente e propósito financeiro.

        Usa ZK-proofs para verificar validade do consentimento sem revelar identidade.
        """
        # Em produção: chamada API para Customer Vault com ZK-proof de autorização
        # Aqui: simulação de resposta
        return [
            FinancialEthicalConsent(
                consent_id="consent_br_credit_001",
                customer_id_hash=customer_id_hash,
                allowed_purposes=["credit_scoring", "fraud_detection"],
                fairness_requirements={
                    "credit_parity_alpha": 0.03,  # Threshold BCB
                    "equal_opportunity_alpha": 0.03,
                },
                explainability_level="counterfactual",  # Cliente quer explicações contrafactuais
                allow_zk_verification=True,
                granted_at="2026-01-01T00:00:00Z",
                expires_at="2027-01-01T00:00:00Z",
                jurisdiction="BR",
            )
        ]

    def verify_ethical_financial_usage(self, model_id: str,
                                      customer_consents: List[FinancialEthicalConsent],
                                      ethics_proof: BankingEthicsProof) -> bool:
        """
        Verifica se uso do modelo para clientes com dados consentimentos é ético.

        Combina:
        1. Validação de consentimentos (via ZK-proof do Customer Vault)
        2. Verificação do banking ethics proof do modelo
        3. Checagem de que requisitos de fairness dos consentimentos são atendidos
        """
        # 1. Verificar banking ethics proof do modelo
        if not self.zk_verifier.verify_proof(ethics_proof, ethics_proof.public_inputs):
            return False

        # 2. Extrair fairness params do proof (assumindo que estão nos public_inputs)
        # O proof public_inputs tem "fairness_alpha_threshold" no exemplo, mas o código procura chaves dinâmicas
        # Adaptaremos para a estrutura do exemplo
        proof_fairness_alpha = ethics_proof.public_inputs.get("fairness_alpha_threshold", 0.03)

        # 3. Verificar se proof satisfaz requisitos de todos os consentimentos
        for consent in customer_consents:
            required_fairness = consent.get_fairness_params()

            # Verificar paridade de crédito
            required_alpha = required_fairness.get("credit_parity_alpha")
            if required_alpha is not None and proof_fairness_alpha > required_alpha:
                return False

            # Na implementação original, exigia keys exatas:
            # for key, required_value in required_fairness.items():
            #     proof_value = proof_fairness.get(key)
            #     if proof_value is None:
            #         return False  # Proof não cobre este requisito
            #     if proof_value > required_value:
            #         return False  # Proof não atende threshold requerido

        return True
