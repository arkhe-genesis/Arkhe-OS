# arkhe_os/banking_ethics_governance/predicates/credit_fairness_predicates.py
"""
Predicados de fairness para verificação de não-discriminação
em modelos de crédito e scoring bancário.
Implementa métricas como paridade demográfica, igualdade de oportunidade,
paridade preditiva adaptadas para contexto financeiro.
"""
from .base_predicate import BankingEthicalPredicate, BankingEthicalPrinciple, BankingVerificationLevel
from sympy import Symbol, Abs, Le, Ge, And, symbols
import numpy as np
from typing import Dict, Any

def demographic_parity_credit_eval(model_state: Dict, data_state: Dict,
                                   value_state: Dict) -> bool:
    """
    Avalia paridade demográfica em aprovação de crédito:
    P(APROVADO|G=g_i) ≈ P(APROVADO|G=g_j) para todos os grupos.

    Args:
        model_state: Contém decisões de crédito por grupo demográfico
        data_state: Contém labels reais e metadados demográficos
        value_state: Contém parâmetros de threshold regulatório (alpha)

    Returns:
        True se diferença máxima entre grupos ≤ alpha (ex: 0.03 para BCB)
    """
    decisions = model_state.get("credit_decisions_by_group", {})
    alpha = value_state.get("credit_fairness_alpha", 0.03)  # Threshold BCB

    if not decisions:
        return False

    # Calcula taxa de aprovação por grupo
    approval_rates = {
        group: np.mean([1 if d == "APPROVED" else 0 for d in group_decisions])
        if len(group_decisions) > 0 else 0.0
        for group, group_decisions in decisions.items()
    }

    # Verifica se diferença máxima entre quaisquer dois grupos ≤ alpha
    rate_values = list(approval_rates.values())
    max_diff = max(rate_values) - min(rate_values) if rate_values else 0.0

    return max_diff <= alpha

def demographic_parity_credit_symbolic(alpha: float = 0.03) -> Any:
    """
    Retorna expressão simbólica para paridade demográfica em crédito.

    Fórmula: |P[APROVADO|G=g_i] - P[APROVADO|G=g_j]| ≤ α ∀ i,j
    """
    # Variáveis simbólicas para taxas de aprovação por grupo
    g1_approval, g2_approval = symbols('g1_approval g2_approval', real=True)

    # Restrição: diferença absoluta ≤ alpha
    constraint = And(
        Le(Abs(g1_approval - g2_approval), alpha),
        Ge(g1_approval, 0), Le(g1_approval, 1),
        Ge(g2_approval, 0), Le(g2_approval, 1)
    )

    return constraint

# Predicado de paridade demográfica para crédito
CREDIT_DEMOGRAPHIC_PARITY_PREDICATE = BankingEthicalPredicate(
    predicate_id="credit_fairness_demo_parity_v1",
    principle=BankingEthicalPrinciple.CREDIT_FAIRNESS,
    name="Credit Demographic Parity",
    description="Credit approval rates should have similar positive rates across demographic groups",
    evaluation_fn=demographic_parity_credit_eval,
    symbolic_expression=demographic_parity_credit_symbolic(),
    parameters={"alpha": 0.03, "groups": ["age", "sex", "ethnicity", "region"]},
    verification_level=BankingVerificationLevel.CERTIFIED,
    references=[
        "BCB Resolução 4.893/2021: Uso de IA em instituições financeiras - Princípio de equidade",
        "Basel Committee on Banking Supervision: Principles for sound management of model risk",
        "EU AI Act Annex III: High-risk AI systems in credit scoring shall avoid bias"
    ]
)

def equal_opportunity_credit_eval(model_state: Dict, data_state: Dict,
                                  value_state: Dict) -> bool:
    """
    Avalia igualdade de oportunidade em crédito:
    P(APROVADO|BOM_PAGADOR=1,G=g_i) ≈ P(APROVADO|BOM_PAGADOR=1,G=g_j).

    Foca em igualdade de true positive rates entre grupos (não discriminar bons pagadores).
    """
    decisions_by_group_label = model_state.get("decisions_by_group_label", {})
    alpha = value_state.get("credit_fairness_alpha", 0.03)

    if not decisions_by_group_label:
        return False

    # Calcula TPR (true positive rate = aprovar bons pagadores) por grupo
    tprs = {}
    for group, data in decisions_by_group_label.items():
        true_positives = sum(1 for d, y in zip(data["decisions"], data["actual_labels"])
                           if d == "APPROVED" and y == "GOOD_PAYER")
        actual_good_payers = sum(1 for y in data["actual_labels"] if y == "GOOD_PAYER")
        tprs[group] = true_positives / actual_good_payers if actual_good_payers > 0 else 0.0

    # Verifica diferença máxima em TPRs
    tpr_values = list(tprs.values())
    max_diff = max(tpr_values) - min(tpr_values) if tpr_values else 0.0

    return max_diff <= alpha

def equal_opportunity_credit_symbolic(alpha: float = 0.03) -> Any:
    """
    Retorna expressão simbólica para igualdade de oportunidade em crédito.
    """
    # Variáveis simbólicas para taxas de aprovação (TPR) por grupo
    g1_tpr, g2_tpr = symbols('g1_tpr g2_tpr', real=True)

    # Restrição: diferença absoluta ≤ alpha
    constraint = And(
        Le(Abs(g1_tpr - g2_tpr), alpha),
        Ge(g1_tpr, 0), Le(g1_tpr, 1),
        Ge(g2_tpr, 0), Le(g2_tpr, 1)
    )

    return constraint

# Predicado de igualdade de oportunidade para crédito
CREDIT_EQUAL_OPPORTUNITY_PREDICATE = BankingEthicalPredicate(
    predicate_id="credit_fairness_equal_opp_v1",
    principle=BankingEthicalPrinciple.CREDIT_FAIRNESS,
    name="Credit Equal Opportunity",
    description="Model should approve good payers at similar rates across demographic groups",
    evaluation_fn=equal_opportunity_credit_eval,
    symbolic_expression=equal_opportunity_credit_symbolic(),
    parameters={"alpha": 0.03, "groups": ["age", "sex", "ethnicity", "region"]},
    verification_level=BankingVerificationLevel.CERTIFIED,
    references=[
        "Hardt et al. (2016): Equality of Opportunity in Supervised Learning (adaptado para crédito)",
        "BCB Circular 3.978/2020: Gestão de riscos em modelos de crédito",
        "CFPB Supervisory Highlights: Fair lending in algorithmic credit decisions"
    ]
)
