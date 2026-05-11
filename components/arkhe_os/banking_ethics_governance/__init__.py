# arkhe_os/banking_ethics_governance/__init__.py
"""
Banking Ethics Governance Engine.
Pilar de Governança Ética Formal para Sistemas Bancários do ARKHE OS.
"""

from .prover.banking_ethics_zk_prover import BankingEthicsZKProver, BankingEthicsProof
from .compiler.predicate_to_ucs_compiler import BankingPredicateToUCSCompiler, BankingUCSConstraint
from .compiler.ucs_to_zinc_compiler import BankingUCSToZincCompiler, BankingZincCircuit
from .integration.customer_vault_adapter import CustomerVaultEthicsAdapter, FinancialEthicalConsent
from .integration.compliance_engine_adapter import BankingComplianceToEthicsMapper

__all__ = [
    "BankingEthicsZKProver",
    "BankingEthicsProof",
    "BankingPredicateToUCSCompiler",
    "BankingUCSConstraint",
    "BankingUCSToZincCompiler",
    "BankingZincCircuit",
    "CustomerVaultEthicsAdapter",
    "FinancialEthicalConsent",
    "BankingComplianceToEthicsMapper",
]
