"""
Arkhe OS Ethics Governance Engine (Substrate 295)
"""
from .predicates.base_predicate import EthicalPredicate, EthicalPrinciple, VerificationLevel
from .compiler.predicate_to_ucs_compiler import PredicateToUCSCompiler, UCSConstraint
from .compiler.ucs_to_zinc_compiler import UCSToZincCompiler, ZincCircuit
from .prover.ethics_zk_prover import EthicsZKProver, EthicsProof
from .integration.patient_vault_adapter import PatientVaultEthicsAdapter, EthicalConsent
from .integration.compliance_engine_adapter import ComplianceToEthicsMapper
from .integration.clinical_simulator_adapter import ClinicalSimulatorEthicsAdapter, EthicalSimulationResult

__all__ = [
    "EthicalPredicate",
    "EthicalPrinciple",
    "VerificationLevel",
    "PredicateToUCSCompiler",
    "UCSConstraint",
    "UCSToZincCompiler",
    "ZincCircuit",
    "EthicsZKProver",
    "EthicsProof",
    "PatientVaultEthicsAdapter",
    "EthicalConsent",
    "ComplianceToEthicsMapper",
    "ClinicalSimulatorEthicsAdapter",
    "EthicalSimulationResult",
]
