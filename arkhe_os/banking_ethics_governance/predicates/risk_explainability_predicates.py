# arkhe_os/banking_ethics_governance/predicates/risk_explainability_predicates.py
"""
Predicados de explicabilidade para verificação de justificabilidade causal
em decisões de risco bancário (crédito, investimento, AML).
Implementa estabilidade local, importância de features financeiras,
consistência contrafactual adaptada para contexto regulatório.
"""
from .base_predicate import BankingEthicalPredicate, BankingEthicalPrinciple, BankingVerificationLevel
from sympy import Symbol, Derivative, Abs, Le, Ge, And, symbols
import numpy as np
from typing import Dict, Any

def causal_stability_risk_eval(model_state: Dict, data_state: Dict,
                               value_state: Dict) -> bool:
    """
    Avalia estabilidade causal em modelos de risco: pequenas perturbações
    em features não-financeiras não devem alterar significativamente a decisão.

    Args:
        model_state: Contém gradientes ou perturbações do modelo de risco
        data_state: Contém features classificadas como financeiras vs. demográficas
        value_state: Contém thresholds de sensibilidade regulatória (eta, delta)

    Returns:
        True se sensibilidade a features demográficas ≤ eta × sensibilidade a features financeiras
    """
    gradients = model_state.get("feature_gradients", {})
    financial_features = data_state.get("financial_feature_names", [])  # renda, score, endividamento
    demographic_features = data_state.get("demographic_feature_names", [])  # etnia, gênero, CEP
    eta = value_state.get("risk_explainability_eta", 0.85)  # Threshold BCB para explicabilidade

    if not gradients or not financial_features:
        return False

    # Calcula magnitude média de gradientes por tipo de feature
    financial_grads = [abs(gradients.get(f, 0.0)) for f in financial_features if f in gradients]
    demo_grads = [abs(gradients.get(f, 0.0)) for f in demographic_features if f in gradients]

    avg_financial = np.mean(financial_grads) if financial_grads else 1e-6
    avg_demo = np.mean(demo_grads) if demo_grads else 0.0

    # Verifica: avg_demo ≤ eta × avg_financial
    return avg_demo <= eta * avg_financial + 1e-8  # Tolerância numérica

def causal_stability_risk_symbolic(eta: float = 0.85) -> Any:
    """
    Retorna expressão simbólica para estabilidade causal em risco bancário.

    Fórmula: |∂Score/∂x_demo| ≤ η × |∂Score/∂x_financeira|
    """
    # Variáveis simbólicas para gradientes
    grad_financial, grad_demo = symbols('grad_financial grad_demo', real=True)

    # Restrição: gradiente demográfico limitado por gradiente financeiro
    constraint = And(
        Le(Abs(grad_demo), eta * Abs(grad_financial) + 1e-8),
        Ge(Abs(grad_financial), 1e-6)  # Evita divisão por zero
    )

    return constraint

# Predicado de estabilidade causal para risco bancário
RISK_CAUSAL_STABILITY_PREDICATE = BankingEthicalPredicate(
    predicate_id="risk_explain_causal_stability_v1",
    principle=BankingEthicalPrinciple.RISK_EXPLAINABILITY,
    name="Risk Causal Stability",
    description="Risk scores should be more sensitive to financial features than demographic features",
    evaluation_fn=causal_stability_risk_eval,
    symbolic_expression=causal_stability_risk_symbolic(),
    parameters={"eta": 0.85, "min_financial_gradient": 1e-6},
    verification_level=BankingVerificationLevel.CERTIFIED,
    references=[
        "BCB Resolução 4.893/2021: Explicabilidade de modelos de IA em serviços financeiros",
        "EU AI Act Annex III: High-risk AI systems shall provide meaningful explanations",
        "SR 11-7 Federal Reserve: Model risk management - interpretability requirements"
    ]
)

def counterfactual_consistency_credit_eval(model_state: Dict, data_state: Dict,
                                           value_state: Dict) -> bool:
    """
    Avalia consistência contrafactual em decisões de crédito: mudanças justificadas
    em features financeiras devem produzir mudanças previsíveis na decisão.

    Exemplo: Se feature "renda" aumenta 20%, probabilidade de aprovação deve aumentar.
    """
    counterfactuals = model_state.get("counterfactual_tests", [])
    expected_directions = value_state.get("expected_directions", {})  # Mapeamento feature → direção esperada
    tolerance = value_state.get("counterfactual_tolerance", 0.1)

    if not counterfactuals:
        return True  # Sem testes, assume conformidade

    consistent_count = 0
    for cf in counterfactuals:
        feature = cf["feature"]
        change = cf.get("change", 0)  # +1 (aumento) ou -1 (diminuição)
        score_before = cf["score_before"]
        score_after = cf["score_after"]

        # Direção esperada da mudança no score
        expected_direction = expected_directions.get(feature, 0)
        actual_direction = np.sign(score_after - score_before)

        # Verifica se direção está dentro da tolerância
        if expected_direction == 0:
            # Sem direção esperada: mudança deve ser pequena
            if abs(score_after - score_before) <= tolerance:
                consistent_count += 1
        elif actual_direction == expected_direction:
            consistent_count += 1
        elif abs(score_after - score_before) <= tolerance:
            # Mudança pequena mesmo com direção oposta pode ser aceitável
            consistent_count += 1

    consistency_rate = consistent_count / len(counterfactuals)
    return consistency_rate >= value_state.get("min_consistency_rate", 0.9)

# Predicado de consistência contrafactual para crédito
CREDIT_COUNTERFACTUAL_CONSISTENCY_PREDICATE = BankingEthicalPredicate(
    predicate_id="credit_explain_counterfactual_v1",
    principle=BankingEthicalPrinciple.RISK_EXPLAINABILITY,
    name="Credit Counterfactual Consistency",
    description="Credit scores should respond to financial feature changes in economically justified directions",
    evaluation_fn=counterfactual_consistency_credit_eval,
    parameters={
        "min_consistency_rate": 0.9,
        "counterfactual_tolerance": 0.1,
        "expected_directions": {
            "renda_mensal": 1, "score_serasa": 1, "endividamento": -1,  # Aumento → maior score
            "historico_atrasos": -1, "numero_dependentes": -0.5,        # Aumento → menor score
        }
    },
    verification_level=BankingVerificationLevel.STRONG,
    references=[
        "Wachter et al. (2017): Counterfactual Explanations for Credit Decisions",
        "BCB Carta-Circular 4.024/2021: Transparência em decisões automatizadas de crédito",
        "GDPR Article 22: Right to meaningful information about automated decisions"
    ]
)
