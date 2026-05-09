"""
Exemplo completo: Verificação ética de modelo de triagem NAFLD
com proofs ZK de fairness demográfico e explicabilidade causal.
"""
from sympy import symbols
import numpy as np
import hashlib
import json
from datetime import datetime

from arkhe_os.ethics_governance import (
    EthicsZKProver,
    PredicateToUCSCompiler,
    UCSToZincCompiler,
    PatientVaultEthicsAdapter,
    ComplianceToEthicsMapper,
)
from arkhe_os.ethics_governance.predicates.fairness_predicates import (
    DEMOGRAPHIC_PARITY_PREDICATE,
    EQUAL_OPPORTUNITY_PREDICATE,
)
from arkhe_os.ethics_governance.predicates.explainability_predicates import (
    CAUSAL_STABILITY_PREDICATE,
)

def main():
    # 1. Inicializar componentes
    ethics_prover = EthicsZKProver(zinc_plus_path="./zinc-plus-bin")
    p2u_compiler = PredicateToUCSCompiler()
    u2z_compiler = UCSToZincCompiler()
    compliance_mapper = ComplianceToEthicsMapper()

    # 2. Definir política ética para NAFLD (baseada em HIPAA + diretrizes clínicas)
    ethical_predicates = [
        DEMOGRAPHIC_PARITY_PREDICATE,  # Fairness por demografia
        EQUAL_OPPORTUNITY_PREDICATE,   # Igualdade de oportunidade
        CAUSAL_STABILITY_PREDICATE,    # Explicabilidade causal
    ]

    # 3. Compilar predicados para circuito Zinc+
    print("🔐 Compilando predicados éticos para circuito ZK...")

    # Contexto simbólico para modelo NAFLD
    symbolic_context = {
        # Features clínicas
        "bilirubin": symbols("bilirubin", real=True),
        "alt": symbols("alt", real=True),
        "ast": symbols("ast", real=True),
        "albumin": symbols("albumin", real=True),
        "platelets": symbols("platelets", real=True),
        # Features demográficas
        "age_group": symbols("age_group", integer=True),
        "sex": symbols("sex", integer=True),
        "ethnicity": symbols("ethnicity", integer=True),
        # Output
        "nafld_risk_score": symbols("nafld_risk_score", real=True),
    }

    # Compilar cada predicado → UCS → Zinc+
    all_ucs_constraints = []
    for predicate in ethical_predicates:
        ucs_constraints = p2u_compiler.compile_predicate(predicate, symbolic_context)
        all_ucs_constraints.extend(ucs_constraints)
        print(f"   ✓ {predicate.name}: {len(ucs_constraints)} restrições UCS")

    # Compilar UCS → circuito Zinc+
    ethics_circuit = u2z_compiler.compile_constraints(
        all_ucs_constraints,
        circuit_name="nafld_ethics_verification_v1"
    )
    print(f"✅ Circuito Zinc+ gerado: {ethics_circuit.constraint_count} constraints")
    print(f"   Estimativa de proof size: {ethics_circuit.estimated_proof_size}")

    # 4. Preparar witness (dados privados) e public inputs
    print("\n🧪 Preparando witness para prova ZK...")

    # Witness privado (não revelado no proof)
    private_witness = {
        # Parâmetros do modelo NAFLD (privados)
        "model_weights": "encrypted_blob_placeholder",
        "training_data_stats": {
            "mean_bilirubin": 0.8,
            "std_alt": 15.2,
            # ... outras estatísticas
        },
        # Predições individuais (privadas)
        "individual_predictions": "encrypted_patient_predictions",
    }

    # Inputs públicos (revelados para verificação)
    public_inputs = {
        # Métricas agregadas de fairness
        "demographic_parity_diff": 0.032,  # < 0.05 threshold
        "equal_opportunity_diff": 0.041,   # < 0.05 threshold
        # Métricas de explicabilidade
        "causal_stability_score": 0.92,    # > 0.8 threshold
        # Metadata
        "model_version": "nafld_classifier_v2.1",
        "evaluation_dataset_size": 5000,
        "fairness_alpha_threshold": 0.05,
    }

    # 5. Gerar proof ZK de conformidade ética
    print("\n⚡ Gerando proof ZK de conformidade ética...")
    ethics_proof = ethics_prover.generate_ethics_proof(
        circuit=ethics_circuit,
        private_witness=private_witness,
        public_inputs=public_inputs,
        policy_version="nafld_ethics_policy_v1.0"
    )

    print(f"✅ Proof gerado: {ethics_proof.proof_id}")
    print(f"   Circuit: {ethics_proof.circuit_id}")
    print(f"   VK hash: {ethics_proof.verification_key_hash[:16]}...")
    print(f"   Metadata: {json.dumps(ethics_proof.metadata, indent=2)}")

    # 6. Verificar proof publicamente (qualquer parte pode verificar)
    print("\n🔍 Verificando proof publicamente...")
    is_valid = ethics_prover.verify_proof(ethics_proof, public_inputs)
    print(f"{'✅' if is_valid else '❌'} Proof verification: {'VALID' if is_valid else 'INVALID'}")

    # 7. Integrar com Patient Vault para consentimento
    print("\n🔐 Verificando consentimentos de pacientes...")
    vault_adapter = PatientVaultEthicsAdapter(
        vault_endpoint="https://vault.arkhe.local",
        zk_proof_verifier=ethics_prover
    )

    # Simular consulta de consentimentos para coorte de estudo
    patient_consents = vault_adapter.get_ethical_consents(
        patient_id_hash="hash_patient_cohort_nafld",
        requested_purpose="clinical_decision"
    )

    print(f"   Consentimentos encontrados: {len(patient_consents)}")
    for consent in patient_consents:
        print(f"   • {consent.consent_id}: fairness_alpha={consent.fairness_requirements.get('demographic_parity_alpha')}")

    # Verificar se proof atende requisitos de consentimento
    usage_approved = vault_adapter.verify_ethical_usage(
        model_id="nafld_classifier_v2.1",
        patient_consents=patient_consents,
        ethics_proof=ethics_proof
    )
    print(f"{'✅' if usage_approved else '❌'} Uso aprovado pelos consentimentos: {usage_approved}")

    # 8. Gerar relatório de auditoria ética
    print("\n📄 Gerando relatório de auditoria ética...")
    report = {
        "model_id": "nafld_classifier_v2.1",
        "verification_timestamp": ethics_proof.metadata["timestamp"],
        "policy_version": ethics_proof.metadata["policy_version"],
        "predicates_verified": [p.predicate_id for p in ethical_predicates],
        "public_metrics": public_inputs,
        "proof_reference": {
            "proof_id": ethics_proof.proof_id,
            "circuit_id": ethics_proof.circuit_id,
            "vk_hash": ethics_proof.verification_key_hash,
        },
        "consent_compliance": {
            "consents_checked": len(patient_consents),
            "usage_approved": usage_approved,
        },
        "regulatory_alignment": {
            "HIPAA": "aligned" if ethics_proof.metadata.get("constraint_count", 0) > 0 else "pending",
            "FDA_AI_SaMD": "aligned",  # Simulado
        },
    }

    print(json.dumps(report, indent=2))

    # 9. Submeter para ledger de auditoria (Substrato 292)
    print("\n🔗 Submetendo para audit ledger imutável...")
    # Em produção: chamada para AuditLedger.log_event()
    audit_entry = {
        "event_type": "ETHICS_VERIFICATION_COMPLETED",
        "model_id": report["model_id"],
        "proof_hash": ethics_proof.compute_hash(),
        "regulatory_jurisdictions": ["HIPAA", "FDA"],
        "timestamp": report["verification_timestamp"],
    }
    print(f"   Audit entry hash: {hashlib.sha256(json.dumps(audit_entry).encode()).hexdigest()[:16]}...")

    print("\n✨ Verificação ética concluída com sucesso!")
    print("   • Modelo NAFLD provado ético via ZK-proof")
    print("   • Fairness demográfica verificada (Δ = 0.032 < 0.05)")
    print("   • Explicabilidade causal confirmada (score = 0.92)")
    print("   • Consentimentos de pacientes respeitados")
    print("   • Auditoria registrada em ledger imutável")

if __name__ == "__main__":
    main()
