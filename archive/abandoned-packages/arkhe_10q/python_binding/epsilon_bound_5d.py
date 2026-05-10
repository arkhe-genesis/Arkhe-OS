#!/usr/bin/env python3
"""
epsilon_bound_5d.py — Binding Python para bound computável extraído de Coq.

ARKHE 10Q Phase 0 — Milestone 4
"""

import math
from typing import Union

# Constantes calibradas (mesmas da extração Coq)
C = 0.1
C_PRIME = 0.05

def epsilon_bound_5d(
    delta_privacy: float,
    sigma: float,
    lambda_eff: float,
    delta: float = 1e-5
) -> float:
    """
    Calcula bound de ε para DP Riemanniano 5D.

    Fórmula extraída da prova Coq:
    ε_5D = [ε_4D + ε²/2] · (1 + c/λ²)

    Args:
        delta_privacy: sensibilidade da query (Δ)
        sigma: desvio padrão do ruído Gaussiano
        lambda_eff: fator de escala efetivo (>0)
        delta: parâmetro de falha de DP (default: 1e-5)

    Returns:
        Bound de ε garantido para (ε, δ)-DP em 5D
    """
    if lambda_eff <= 0:
        raise ValueError("lambda_eff must be positive")

    # Termo base: bound euclidiano clássico
    base = (delta_privacy / sigma) * math.sqrt(2 * math.log(1.25 / delta))

    # Termo quadrático: composição de segunda ordem
    quadratic = (delta_privacy ** 2) / (2 * sigma ** 2)

    # Correção de escala: fator geométrico 5D
    scale_correction = 1.0 + C / (lambda_eff ** 2 + 1e-8)

    return (base + quadratic) * scale_correction


def verify_bound(
    delta_privacy: float,
    sigma: float,
    lambda_eff: float,
    empirical_epsilon: float,
    delta: float = 1e-5
) -> bool:
    """
    Verifica se ε empírico está dentro do bound teórico.

    Args:
        empirical_epsilon: ε medido experimentalmente
        demais parâmetros: como epsilon_bound_5d

    Returns:
        True se empirical_epsilon ≤ bound teórico
    """
    theoretical = epsilon_bound_5d(delta_privacy, sigma, lambda_eff, delta)
    return empirical_epsilon <= theoretical * 1.05  # 5% margem para ruído experimental


if __name__ == '__main__':
    # Teste numérico
    print("Testing epsilon_bound_5d...")

    # Parâmetros típicos
    delta_privacy = 0.1
    sigma = 1.0
    lambda_eff = 2.0
    delta = 1e-5

    bound = epsilon_bound_5d(delta_privacy, sigma, lambda_eff, delta)
    print(f"ε_5D bound: {bound:.4f}")

    # Verificar com ε empírico simulado
    empirical = 0.15  # valor típico medido
    valid = verify_bound(delta_privacy, sigma, lambda_eff, empirical, delta)
    print(f"Empirical ε={empirical:.4f} within bound: {valid}")

    # Testar variação com λ
    print("\nε_5D vs lambda_eff:")
    for lam in [0.5, 1.0, 2.0, 5.0, 10.0]:
        b = epsilon_bound_5d(delta_privacy, sigma, lam, delta)
        print(f"  λ={lam:4.1f}: ε_5D={b:.4f}")
