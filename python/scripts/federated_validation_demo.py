# federated_validation_demo.py — Exemplo de uso
from arkhe_os.federated_validation import (
    FederatedValidationCoordinator,
    FHEValidationEngine,
    FederatedDPCalibrator,
    ZKConsensusProver,
)
from arkhe_os.validation.experimental_harness import ExperimentalValidationHarness

# Inicializar componentes
coordinator = FederatedValidationCoordinator(federation_id="fed-quantum-materials-2026")
fhe_engine = FHEValidationEngine(default_params=None)  # Configurar parâmetros CKKS
dp_calibrator = FederatedDPCalibrator(lab_configs={})  # Configurar por laboratório
zk_prover = ZKConsensusProver()

# Configurar round federado
round_config = {
    "round_id": "round_001",
    "validation_type": "susceptibility",
    "target_material": "herbertsmithite",
    "num_labs": 5,
    "epsilon_global": 1.0,
    "delta": 1e-5,
    "jurisdictions": ["BR", "EU", "US"],
    "compliance_predicates": ["FAIR", "GDPR", "reproducibility"],
}

# Coordenar round federado
results = coordinator.run_federated_round(
    round_config=round_config,
    validation_harness=ExperimentalValidationHarness(),
    fhe_engine=fhe_engine,
    dp_calibrator=dp_calibrator,
    zk_prover=zk_prover,
)

print(f"✅ Round federado concluído: {results['global_coherence']:.3f} ± {results['std_coherence']:.3f}")
print(f"🔐 Proof de consenso: {results['consensus_proof_id']}")
print(f"📊 Laboratórios participantes: {results['participating_labs']}")
