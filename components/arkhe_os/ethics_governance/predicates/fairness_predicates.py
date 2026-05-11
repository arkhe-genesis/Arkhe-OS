"""
Predicados de fairness para verificação de não-discriminação em modelos de IA em saúde.
Implementa métricas como paridade demográfica, igualdade de oportunidade, paridade preditiva.
"""
from typing import Dict, Any
from .base_predicate import EthicalPredicate, EthicalPrinciple, VerificationLevel
from sympy import Symbol, Abs, Le, Ge, And, symbols
import numpy as np

def demographic_parity_eval(model_state: Dict, data_state: Dict,
                           value_state: Dict) -> bool:
    """
    Avalia paridade demográfica: P(M=1|G=g_i) ≈ P(M=1|G=g_j) para todos os grupos.

    Args:
        model_state: Contém predições do modelo por grupo demográfico
        data_state: Contém labels verdadeiros e metadados demográficos
        value_state: Contém parâmetros de threshold (alpha)

    Returns:
        True se diferença máxima entre grupos ≤ alpha
    """
    predictions = model_state.get("predictions_by_group", {})
    alpha = value_state.get("fairness_alpha", 0.05)

    if not predictions:
        return False

    # Calcula taxa de predição positiva por grupo
    rates = {
        group: np.mean(preds) if len(preds) > 0 else 0.0
        for group, preds in predictions.items()
    }

    # Verifica se diferença máxima entre quaisquer dois grupos ≤ alpha
    rate_values = list(rates.values())
    max_diff = max(rate_values) - min(rate_values) if rate_values else 0.0

    return max_diff <= alpha

def demographic_parity_symbolic(alpha: float = 0.05) -> Any:
    """
    Retorna expressão simbólica para paridade demográfica.

    Fórmula: |E[M|G=g_i] - E[M|G=g_j]| ≤ α ∀ i,j
    """
    # Variáveis simbólicas para taxas por grupo
    g1_rate, g2_rate = symbols('g1_rate g2_rate', real=True)

    # Restrição: diferença absoluta ≤ alpha
    constraint = And(
        Le(Abs(g1_rate - g2_rate), alpha),
        Ge(g1_rate, 0), Le(g1_rate, 1),
        Ge(g2_rate, 0), Le(g2_rate, 1)
    )

    return constraint

# Predicado de paridade demográfica
DEMOGRAPHIC_PARITY_PREDICATE = EthicalPredicate(
    predicate_id="fairness_demo_parity_v1",
    principle=EthicalPrinciple.FAIRNESS,
    name="Demographic Parity",
    description="Model predictions should have similar positive rates across demographic groups",
    evaluation_fn=demographic_parity_eval,
    symbolic_expression=demographic_parity_symbolic(),
    parameters={"alpha": 0.05, "groups": ["age", "sex", "ethnicity"]},
    verification_level=VerificationLevel.CERTIFIED,
    references=[
        "EU AI Act Article 10: High-risk AI systems shall be designed to avoid bias",
        "WHO Ethics & Governance of AI for Health: Principle of equity"
    ]
)

def equal_opportunity_eval(model_state: Dict, data_state: Dict,
                          value_state: Dict) -> bool:
    """
    Avalia igualdade de oportunidade: P(M=1|Y=1,G=g_i) ≈ P(M=1|Y=1,G=g_j).

    Foca em igualdade de true positive rates entre grupos.
    """
    predictions = model_state.get("predictions_by_group_label", {})
    alpha = value_state.get("fairness_alpha", 0.05)

    if not predictions:
        return False

    # Calcula TPR (true positive rate) por grupo
    tprs = {}
    for group, data in predictions.items():
        true_positives = sum(1 for p, y in zip(data["preds"], data["labels"]) if p == 1 and y == 1)
        actual_positives = sum(1 for y in data["labels"] if y == 1)
        tprs[group] = true_positives / actual_positives if actual_positives > 0 else 0.0

    # Verifica diferença máxima em TPRs
    tpr_values = list(tprs.values())
    max_diff = max(tpr_values) - min(tpr_values) if tpr_values else 0.0

    return max_diff <= alpha

# Predicado de igualdade de oportunidade
EQUAL_OPPORTUNITY_PREDICATE = EthicalPredicate(
    predicate_id="fairness_equal_opp_v1",
    principle=EthicalPrinciple.FAIRNESS,
    name="Equal Opportunity",
    description="Model should have similar true positive rates across demographic groups",
    evaluation_fn=equal_opportunity_eval,
    symbolic_expression=demographic_parity_symbolic(), # Mock using parity
    parameters={"alpha": 0.05, "groups": ["age", "sex", "ethnicity"]},
    verification_level=VerificationLevel.CERTIFIED,
    references=[
        "Hardt et al. (2016): Equality of Opportunity in Supervised Learning",
        "FDA AI/ML Software as a Medical Device: Bias mitigation requirements"
    ]
)
