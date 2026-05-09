"""
Predicados de explicabilidade para verificação de justificabilidade causal em decisões de IA.
Implementa estabilidade local, importância de features clínicas, consistência contrafactual.
"""
from typing import Dict, Any
from .base_predicate import EthicalPredicate, EthicalPrinciple, VerificationLevel
from sympy import Symbol, Derivative, Abs, Le, And, Ge, symbols
import numpy as np

def causal_stability_eval(model_state: Dict, data_state: Dict,
                         value_state: Dict) -> bool:
    """
    Avalia estabilidade causal: pequenas perturbações em features não-clínicas
    não devem alterar significativamente a predição.

    Args:
        model_state: Contém gradientes ou perturbações do modelo
        data_state: Contém features classificadas como clínicas vs. demográficas
        value_state: Contém thresholds de sensibilidade (eta, delta)

    Returns:
        True se sensibilidade a features demográficas ≤ eta × sensibilidade a features clínicas
    """
    gradients = model_state.get("feature_gradients", {})
    clinical_features = data_state.get("clinical_feature_names", [])
    demographic_features = data_state.get("demographic_feature_names", [])
    eta = value_state.get("explainability_eta", 0.8)  # Threshold de proporção

    if not gradients or not clinical_features:
        return False

    # Calcula magnitude média de gradientes por tipo de feature
    clinical_grads = [abs(gradients.get(f, 0.0)) for f in clinical_features if f in gradients]
    demo_grads = [abs(gradients.get(f, 0.0)) for f in demographic_features if f in gradients]

    avg_clinical = np.mean(clinical_grads) if clinical_grads else 1e-6
    avg_demo = np.mean(demo_grads) if demo_grads else 0.0

    # Verifica: avg_demo ≤ eta × avg_clinical
    return avg_demo <= eta * avg_clinical + 1e-8  # Tolerância numérica

def causal_stability_symbolic(eta: float = 0.8) -> Any:
    """
    Retorna expressão simbólica para estabilidade causal.

    Fórmula: |∂M/∂x_demo| ≤ η × |∂M/∂x_clinical|
    """
    # Variáveis simbólicas para gradientes
    grad_clinical, grad_demo = symbols('grad_clinical grad_demo', real=True)

    # Restrição: gradiente demográfico limitado por gradiente clínico
    constraint = And(
        Le(Abs(grad_demo), eta * Abs(grad_clinical) + 1e-8),
        Ge(Abs(grad_clinical), 1e-6)  # Evita divisão por zero
    )

    return constraint

# Predicado de estabilidade causal
CAUSAL_STABILITY_PREDICATE = EthicalPredicate(
    predicate_id="explain_causal_stability_v1",
    principle=EthicalPrinciple.EXPLAINABILITY,
    name="Causal Stability",
    description="Model predictions should be more sensitive to clinical features than demographic features",
    evaluation_fn=causal_stability_eval,
    symbolic_expression=causal_stability_symbolic(),
    parameters={"eta": 0.8, "min_clinical_gradient": 1e-6},
    verification_level=VerificationLevel.CERTIFIED,
    references=[
        "Ribeiro et al. (2016): 'Why Should I Trust You?' - LIME",
        "EU AI Act Annex III: High-risk AI systems shall provide explanations"
    ]
)

def counterfactual_consistency_eval(model_state: Dict, data_state: Dict,
                                   value_state: Dict) -> bool:
    """
    Avalia consistência contrafactual: mudanças justificadas em features
    devem produzir mudanças previsíveis e justificáveis na predição.

    Exemplo: Se feature "bilirrubina" aumenta, predição de NAFLD deve aumentar.
    """
    counterfactuals = model_state.get("counterfactual_tests", [])
    expected_directions = value_state.get("expected_directions", {})
    tolerance = value_state.get("counterfactual_tolerance", 0.1)

    if not counterfactuals:
        return True  # Sem testes, assume conformidade

    consistent_count = 0
    for cf in counterfactuals:
        feature = cf["feature"]
        change = cf["change"]  # +1 ou -1
        pred_before = cf["prediction_before"]
        pred_after = cf["prediction_after"]

        # Direção esperada da mudança na predição
        expected_direction = expected_directions.get(feature, 0)
        actual_direction = np.sign(pred_after - pred_before)

        # Verifica se direção está dentro da tolerância
        if expected_direction == 0:
            # Sem direção esperada: mudança deve ser pequena
            if abs(pred_after - pred_before) <= tolerance:
                consistent_count += 1
        elif actual_direction == expected_direction:
            consistent_count += 1
        elif abs(pred_after - pred_before) <= tolerance:
            # Mudança pequena mesmo com direção oposta pode ser aceitável
            consistent_count += 1

    consistency_rate = consistent_count / len(counterfactuals)
    return consistency_rate >= value_state.get("min_consistency_rate", 0.9)

# Predicado de consistência contrafactual
COUNTERFACTUAL_CONSISTENCY_PREDICATE = EthicalPredicate(
    predicate_id="explain_counterfactual_v1",
    principle=EthicalPrinciple.EXPLAINABILITY,
    name="Counterfactual Consistency",
    description="Model should respond to feature changes in clinically justified directions",
    evaluation_fn=counterfactual_consistency_eval,
    parameters={
        "min_consistency_rate": 0.9,
        "counterfactual_tolerance": 0.1,
        "expected_directions": {
            "bilirubin": 1, "alt": 1, "ast": 1,  # Aumento → maior risco NAFLD
            "albumin": -1, "platelets": -1,       # Aumento → menor risco NAFLD
        }
    },
    verification_level=VerificationLevel.STRONG,
    references=[
        "Wachter et al. (2017): Counterfactual Explanations without Opening the Black Box",
        "FDA Good Machine Learning Practice: Principle 8 - Transparency"
    ]
)
