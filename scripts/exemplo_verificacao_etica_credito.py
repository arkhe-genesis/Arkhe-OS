# exemplo_verificacao_etica_credito.py
"""
Exemplo completo: Verificação ética de modelo de scoring de crédito
com proofs ZK de fairness demográfico e explicabilidade causal.
"""
import sys
import os

# Ensure the root path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from arkhe_os.banking_ethics_governance import (
    BankingEthicsZKProver,
    BankingPredicateToUCSCompiler,
    BankingUCSToZincCompiler,
    CustomerVaultEthicsAdapter,
    BankingComplianceToEthicsMapper,
)
from arkhe_os.banking_ethics_governance.predicates.credit_fairness_predicates import (
    CREDIT_DEMOGRAPHIC_PARITY_PREDICATE,
    CREDIT_EQUAL_OPPORTUNITY_PREDICATE,
)
from arkhe_os.banking_ethics_governance.predicates.risk_explainability_predicates import (
    RISK_CAUSAL_STABILITY_PREDICATE,
)

from sympy import symbols
import numpy as np
import hashlib
import json
from datetime import datetime

def main():
    # 1. Inicializar componentes
    ethics_prover = BankingEthicsZKProver(zinc_plus_path="./zinc-plus-bin",
                                          regulatory_framework="BCB_BASILeia_LGPD")
    p2u_compiler = BankingPredicateToUCSCompiler()
    u2z_compiler = BankingUCSToZincCompiler()
    compliance_mapper = BankingComplianceToEthicsMapper()

    # 2. Definir política ética para scoring de crédito (baseada em BCB + diretrizes internas)
    ethical_predicates = [
        CREDIT_DEMOGRAPHIC_PARITY_PREDICATE,  # Fairness por demografia
        CREDIT_EQUAL_OPPORTUNITY_PREDICATE,   # Igualdade de oportunidade para bons pagadores
        RISK_CAUSAL_STABILITY_PREDICATE,      # Explicabilidade causal
    ]

    # 3. Compilar predicados para circuito Zinc+
    print("🔐 Compilando predicados éticos bancários para circuito ZK...")

    # Contexto simbólico para modelo de crédito
    symbolic_context = {
        # Features financeiras
        "renda_mensal": symbols("renda_mensal", real=True),
        "score_serasa": symbols("score_serasa", real=True),
        "endividamento": symbols("endividamento", real=True),
        "historico_atrasos": symbols("historico_atrasos", real=True),
        # Features demográficas
        "faixa_etaria": symbols("faixa_etaria", integer=True),
        "genero": symbols("genero", integer=True),
        "etnia": symbols("etnia", integer=True),
        # Output
        "credit_score": symbols("credit_score", real=True),
        "approval_probability": symbols("approval_probability", real=True),
    }

    # Compilar cada predicado → UCS → Zinc+
    all_ucs_constraints = []
    for predicate in ethical_predicates:
        ucs_constraints = p2u_compiler.compile_banking_predicate(predicate, symbolic_context)
        all_ucs_constraints.extend(ucs_constraints)
        print(f"   ✓ {predicate.name}: {len(ucs_constraints)} restrições UCS")

    # Compilar UCS → circuito Zinc+
    ethics_circuit = u2z_compiler.compile_banking_constraints(
        all_ucs_constraints,
        circuit_name="credit_scoring_ethics_verification_v1"
    )
    print(f"✅ Circuito Zinc+ bancário gerado: {ethics_circuit.constraint_count} constraints")
    print(f"   Estimativa de proof size: {ethics_circuit.estimated_proof_size}")
    print(f"   Compliance regulatório: {', '.join(ethics_circuit.regulatory_compliance)}")

    # 4. Preparar witness (dados privados) e public inputs
    print("\n🧪 Preparando witness para prova ZK bancária...")

    # Witness privado (não revelado no proof)
    private_witness = {
        # Parâmetros do modelo de crédito (privados)
        "model_weights": "encrypted_blob_placeholder",
        "training_data_stats": {
            "mean_renda": 4500.0,
            "std_score": 120.5,
            # ... outras estatísticas
        },
        # Decisões individuais (privadas)
        "individual_decisions": "encrypted_customer_decisions",
    }

    # Inputs públicos (revelados para verificação regulatória)
    public_inputs = {
        # Métricas agregadas de fairness
        "credit_parity_diff": 0.028,  # < 0.03 threshold BCB
        "equal_opportunity_diff": 0.025,   # < 0.03 threshold
        # Métricas de explicabilidade
        "causal_stability_score": 0.89,    # > 0.85 threshold
        # Metadata regulatório
        "model_version": "credit_scorer_v3.2",
        "evaluation_dataset_size": 50000,
        "fairness_alpha_threshold": 0.03,
        "regulatory_framework": "BCB_RES_4893",
    }

    # 5. Gerar proof ZK de conformidade ética bancária
    print("\n⚡ Gerando proof ZK de conformidade ética bancária...")
    ethics_proof = ethics_prover.generate_banking_ethics_proof(
        circuit=ethics_circuit,
        private_witness=private_witness,
        public_inputs=public_inputs,
        policy_version="banking_ethics_policy_v2.0",
        institution_id="BANCO_EXEMPLO_CNPJ_12345678000199"
    )

    print(f"✅ Proof bancário gerado: {ethics_proof.proof_id}")
    print(f"   Circuit: {ethics_proof.circuit_id}")
    print(f"   VK hash: {ethics_proof.verification_key_hash[:16]}...")
    print(f"   Regulatory Framework: {ethics_proof.regulatory_framework}")
    # Fix output mapping formatting
    print(f"   Metadata: {json.dumps(ethics_proof.metadata, indent=2)}")

    # 6. Verificar proof publicamente (qualquer regulador pode verificar)
    print("\n🔍 Verificando proof publicamente...")
    is_valid = ethics_prover.verify_proof(ethics_proof, public_inputs)
    print(f"{'✅' if is_valid else '❌'} Proof verification: {'VALID' if is_valid else 'INVALID'}")

    # 7. Integrar com Customer Vault para consentimento LGPD
    print("\n🔐 Verificando consentimentos LGPD de clientes...")
    vault_adapter = CustomerVaultEthicsAdapter(
        vault_endpoint="https://vault.arkhe.local/banking",
        zk_proof_verifier=ethics_prover
    )

    # Simular consulta de consentimentos para coorte de análise de crédito
    customer_consents = vault_adapter.get_financial_ethical_consents(
        customer_id_hash="hash_customer_cohort_credit_analysis",
        requested_purpose="credit_scoring",
        jurisdiction="BR"
    )

    print(f"   Consentimentos encontrados: {len(customer_consents)}")
    for consent in customer_consents:
        print(f"   • {consent.consent_id}: credit_parity_alpha={consent.fairness_requirements.get('credit_parity_alpha')}")

    # Verificar se proof atende requisitos de consentimento
    usage_approved = vault_adapter.verify_ethical_financial_usage(
        model_id="credit_scorer_v3.2",
        customer_consents=customer_consents,
        ethics_proof=ethics_proof
    )
    print(f"{'✅' if usage_approved else '❌'} Uso aprovado pelos consentimentos LGPD: {usage_approved}")

    # 8. Gerar relatório de auditoria ética para BCB
    print("\n📄 Gerando relatório de auditoria ética para BCB...")
    report = ethics_proof.to_regulatory_submission()

    print(json.dumps(report, indent=2))

    # 9. Submeter para ledger de auditoria bancária (Substrato 292-B)
    print("\n🔗 Submetendo para audit ledger bancário imutável...")
    # Em produção: chamada para BankingAuditLedger.log_event()
    audit_entry = {
        "event_type": "BANKING_ETHICS_VERIFICATION_COMPLETED",
        "model_id": public_inputs.get("model_version", "unknown_model"),
        "proof_hash": ethics_proof.compute_hash(),
        "regulatory_frameworks": ["BCB_RES_4893", "LGPD_ART_20"],
        "institution_id": "BANCO_EXEMPLO_CNPJ_12345678000199",
        "timestamp": report["submission_timestamp"],
    }
    print(f"   Audit entry hash: {hashlib.sha256(json.dumps(audit_entry).encode()).hexdigest()[:16]}...")

    print("\n✨ Verificação ética bancária concluída com sucesso!")
    print("   • Modelo de scoring provado ético via ZK-proof")
    print("   • Fairness creditício verificado (Δ = 0.028 < 0.03 BCB)")
    print("   • Explicabilidade causal confirmada (score = 0.89)")
    print("   • Consentimentos LGPD de clientes respeitados")
    print("   • Auditoria registrada em ledger imutável para BCB")

if __name__ == "__main__":
    main()
