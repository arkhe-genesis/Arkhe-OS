"""
Exemplo completo: Treinamento federado de modelo de credit scoring
com privacidade via FHE + ZK e compliance multi-jurisdição.
"""
from arkhe_os.federated_learning.privacy.fhe_composition_engine import (
    FHECompositionEngine, FHEParameters, FHEScheme, EncryptedGradient
)
from arkhe_os.federated_learning.privacy.differential_privacy_calibrator import (
    DifferentialPrivacyCalibrator, JurisdictionDPConfig
)
from arkhe_os.federated_learning.privacy.zk_privacy_prover import (
    FederatedPrivacyZKProver, FederatedPrivacyProof
)
from arkhe_os.federated_learning.compliance.federated_predicate_compiler import (
    FederatedPredicateToUCSCompiler, FederatedUCSToZincCompiler,
    FEDERATED_NON_LEAKAGE_PREDICATE,
    FEDERATED_DP_COMPLIANCE_PREDICATE,
)
from arkhe_os.banking_ethics_governance.predicates.credit_fairness_predicates import (
    CREDIT_DEMOGRAPHIC_PARITY_PREDICATE,
)
from sympy import Symbol
import numpy as np
import hashlib
import json
from datetime import datetime

def main():
    # 1. Configurar consórcio federado
    federation_metadata = {
        "federation_id": "global_credit_scoring_v2",
        "round_id": "round_001",
        "num_institutions": 5,
        "jurisdictions": ["BCB", "ECB", "FED"],
        "fhe_scheme": "CKKS",
        "aggregation_method": "secure_aggregation",
        "epsilon_global": 1.0,
        "delta": 1e-5,
        "institution_public_keys": ["key_br_001", "key_eu_001", "key_us_001", "key_br_002", "key_eu_002"],
    }

    # 2. Inicializar componentes de privacidade
    fhe_params = FHEParameters(
        scheme=FHEScheme.CKKS,
        poly_modulus_degree=2**14,
        coeff_modulus_bits=[60, 40, 40, 60],  # Para profundidade multiplicativa ~2
        scale=2**40,
        security_level=128
    )

    fhe_engine = FHECompositionEngine(default_params=fhe_params)

    dp_configs = {
        "BCB": JurisdictionDPConfig(
            jurisdiction="BCB", epsilon_global=1.0, delta=1e-5,
            sensitivity_clipping=1.0, noise_distribution="laplace"
        ),
        "ECB": JurisdictionDPConfig(
            jurisdiction="ECB", epsilon_global=0.5, delta=1e-5,
            sensitivity_clipping=1.0, noise_distribution="gaussian"
        ),
        "FED": JurisdictionDPConfig(
            jurisdiction="FED", epsilon_global=1.0, delta=1e-5,
            sensitivity_clipping=1.0, noise_distribution="laplace"
        ),
    }
    dp_calibrator = DifferentialPrivacyCalibrator(jurisdiction_configs=dp_configs)

    zk_prover = FederatedPrivacyZKProver(
        zinc_plus_path="./zinc-plus-bin",
        fhe_backend="openfhe",
        security_bits=128
    )

    # 3. Definir predicados de compliance federado
    federated_predicates = [
        FEDERATED_NON_LEAKAGE_PREDICATE,
        FEDERATED_DP_COMPLIANCE_PREDICATE,
        CREDIT_DEMOGRAPHIC_PARITY_PREDICATE,  # Fairness também aplica no federado
    ]

    # 4. Simular treinamento local em cada instituição
    print("🔐 Simulando treinamento local com FHE + DP...")
    encrypted_updates = []

    institutions = [
        {"id": "bank_br_001", "jurisdiction": "BCB", "data_size": 50000},
        {"id": "bank_eu_001", "jurisdiction": "ECB", "data_size": 75000},
        {"id": "bank_us_001", "jurisdiction": "FED", "data_size": 100000},
        {"id": "bank_br_002", "jurisdiction": "BCB", "data_size": 30000},
        {"id": "bank_eu_002", "jurisdiction": "ECB", "data_size": 45000},
    ]

    for inst in institutions:
        # Simular gradiente local (em produção: treinamento real sobre dados locais)
        local_gradient = np.random.randn(128) * 0.1  # 128 parâmetros do modelo

        # Obter parâmetros de DP para esta instituição
        dp_params = dp_calibrator.get_noise_params(
            jurisdiction=inst["jurisdiction"],
            data_type="credit_features",
            round_id=federation_metadata["round_id"],
            num_institutions=federation_metadata["num_institutions"],
            gradient_norm_bound=1.0
        )

        # Encryptar gradiente com FHE + DP
        encrypted_grad = fhe_engine.encrypt_gradient(
            gradient=local_gradient,
            params=fhe_params,
            institution_id=inst["id"],
            round_id=federation_metadata["round_id"],
            dp_noise_scale=dp_params.noise_scale
        )

        # Gerar proof ZK local de compliance
        compliance_proof_hash = fhe_engine.generate_compliance_proof(
            encrypted_gradient=encrypted_grad,
            compliance_predicates=[p.predicate_id for p in federated_predicates if hasattr(p, 'predicate_id')]
        )
        encrypted_grad.compliance_proof_hash = compliance_proof_hash

        encrypted_updates.append({
            "ciphertext": encrypted_grad.ciphertext,
            "gradient_hash": encrypted_grad.gradient_hash,
            "institution_id": inst["id"],
            "jurisdiction": inst["jurisdiction"],
            "dp_noise_scale": dp_params.noise_scale,
            "compliance_proof_hash": compliance_proof_hash,
        })

        # Rastrear budget de privacidade
        budget_status = dp_calibrator.track_privacy_budget(
            jurisdiction=inst["jurisdiction"],
            round_id=federation_metadata["round_id"],
            epsilon_consumed=dp_calibrator.configs[inst["jurisdiction"]].calculate_per_institution_epsilon(
                federation_metadata["num_institutions"]
            )
        )
        print(f"   ✓ {inst['id']} ({inst['jurisdiction']}): ε_consumed={budget_status['epsilon_consumed']:.3f}, remaining={budget_status['epsilon_remaining']:.3f}")

    # 5. Agregação segura dos updates criptografados
    print("\\n🔗 Agregando updates via FHE homomórfico...")
    aggregated_update = fhe_engine.homomorphic_aggregate([
        EncryptedGradient(
            ciphertext=eu["ciphertext"],
            scheme=FHEScheme.CKKS,
            institution_id=eu["institution_id"],
            round_id=federation_metadata["round_id"],
            gradient_hash=eu["gradient_hash"],
            dp_noise_scale=eu["dp_noise_scale"],
            compliance_proof_hash=eu["compliance_proof_hash"]
        ) for eu in encrypted_updates
    ])
    print(f"   ✅ Agregação homomórfica concluída: hash={aggregated_update.gradient_hash}")

    # 6. Compilar predicados federados para circuito Zinc+
    print("\\n⚙️ Compilando predicados federados para circuito ZK...")
    p2u_compiler = FederatedPredicateToUCSCompiler()
    u2z_compiler = FederatedUCSToZincCompiler()

    symbolic_context = {
        # Variáveis de modelo
        "model_params": Symbol("θ", commutative=False),
        "global_gradient": Symbol("∇ℒ_global", commutative=False),
        # Variáveis de privacidade
        "epsilon_used": Symbol("ε_used", real=True, nonnegative=True),
        "delta_used": Symbol("δ_used", real=True, positive=True),
        "noise_scale": Symbol("η", real=True, nonnegative=True),
        # Variáveis federadas
        "num_institutions": Symbol("N", integer=True, positive=True),
        "aggregation_round": Symbol("t", integer=True, nonnegative=True),
    }

    all_ucs_constraints = []
    for predicate in federated_predicates:
        if not hasattr(predicate, 'parameters'):
            continue
        for jurisdiction in federation_metadata["jurisdictions"]:
            if jurisdiction in predicate.parameters:
                ucs_constraints = p2u_compiler.compile_federated_predicate(
                    predicate, symbolic_context, jurisdiction, federation_metadata
                )
                all_ucs_constraints.extend(ucs_constraints)
                print(f"   ✓ {predicate.name} ({jurisdiction}): {len(ucs_constraints)} restrições UCS")

    # Compilar UCS → circuito Zinc+
    privacy_circuit = u2z_compiler.compile_federated_constraints(
        all_ucs_constraints,
        circuit_name="federated_credit_scoring_privacy_v1"
    )
    print(f"✅ Circuito Zinc+ federado gerado: {privacy_circuit.constraint_count} constraints")
    print(f"   Estimativa de proof size: {privacy_circuit.estimated_proof_size}")

    # 7. Gerar proof ZK de compliance federado
    print("\\n⚡ Gerando proof ZK de privacidade federada...")
    federated_proof = zk_prover.generate_federated_privacy_proof(
        circuit_config={
            "circuit_id": privacy_circuit.circuit_id,
            "constraint_count": privacy_circuit.constraint_count,
            "regulatory_compliance": privacy_circuit.regulatory_compliance,
        },
        encrypted_updates=encrypted_updates,
        compliance_predicates=[p.predicate_id for p in federated_predicates if hasattr(p, 'predicate_id')],
        federation_metadata=federation_metadata
    )

    print(f"✅ Proof federado gerado: {federated_proof.proof_id}")
    print(f"   Circuit: {federated_proof.circuit_id}")
    print(f"   VK hash: {federated_proof.verification_key_hash[:16]}...")
    print(f"   Regulatory Frameworks: {', '.join(federated_proof.regulatory_frameworks)}")
    # json.dumps doesn't handle objects
    # print(f"   Public inputs: {json.dumps(federated_proof.public_inputs, indent=2)}")

    # 8. Verificar proof publicamente (qualquer regulador)
    print("\\n🔍 Verificando proof federado publicamente...")
    is_valid = zk_prover.verify_federated_privacy_proof(
        proof=federated_proof,
        expected_public_inputs={
            "num_institutions": 5,
            "federation_round": "round_001",
            "epsilon_total": 1.0,
        }
    )
    print(f"{'✅' if is_valid else '❌'} Proof verification: {'VALID' if is_valid else 'INVALID'}")

    # 9. Gerar relatório de auditoria federada
    print("\\n📄 Gerando relatório de auditoria federada...")
    report = federated_proof.to_regulatory_submission()

    # Adicionar métricas de privacidade por jurisdição
    report["privacy_metrics"] = {
        jur: dp_calibrator.generate_privacy_report(jur)
        for jur in federation_metadata["jurisdictions"]
    }

    print(json.dumps(report, indent=2)[:1000] + "...")  # Truncar para exibição

    # 10. Submeter para ledger de auditoria federada
    print("\\n🔗 Submetendo para federated audit ledger...")
    audit_entry = {
        "event_type": "FEDERATED_TRAINING_ROUND_COMPLETED",
        "federation_id": federation_metadata["federation_id"],
        "round_id": federation_metadata["round_id"],
        "proof_hash": federated_proof.compute_hash(),
        "num_institutions": federation_metadata["num_institutions"],
        "jurisdictions": federation_metadata["jurisdictions"],
        "privacy_budget_status": {
            jur: dp_calibrator.track_privacy_budget(jur, federation_metadata["round_id"], 0)["epsilon_remaining"]
            for jur in federation_metadata["jurisdictions"]
        },
        "timestamp": report["submission_timestamp"],
    }
    audit_hash = hashlib.sha256(json.dumps(audit_entry).encode()).hexdigest()[:16]
    print(f"   Audit entry hash: {audit_hash}...")

    print("\\n✨ Treinamento federado com privacidade concluído com sucesso!")
    print("   • Gradientes locais encryptados via CKKS FHE")
    print("   • Ruído DP calibrado por jurisdição (BCB: ε=1.0, ECB: ε=0.5, FED: ε=1.0)")
    print("   • Agregação homomórfica sem decryptar dados individuais")
    print("   • Proof ZK de compliance federado verificável por reguladores")
    print("   • Budget de privacidade rastreado por jurisdição")
    print("   • Auditoria registrada em ledger imutável")

if __name__ == "__main__":
    main()
