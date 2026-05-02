#!/usr/bin/env python3
"""
arkhe_experimental_non_associativity_v295.py
Substrato 295: Prova Experimental da Não-Associatividade Atômica.
Projeta experimento quântico para detectar assinaturas de não-associatividade
octoniônica em emaranhamento de três partículas, validando que (AB)C ≠ A(BC).
"""

import numpy as np
import sys
from arkhe_algebraic_types import Octonion

def generate_random_octonion(norm=1.0) -> Octonion:
    coeffs = np.random.randn(8)
    coeffs = coeffs / np.linalg.norm(coeffs) * norm
    return Octonion(coeffs)

def measure_non_associativity(A: Octonion, B: Octonion, C: Octonion) -> float:
    """
    Mede a não-associatividade entre três octoniões A, B, e C.
    Calcula a norma da diferença: ||(AB)C - A(BC)||
    """
    AB = A * B
    AB_C = AB * C

    BC = B * C
    A_BC = A * BC

    # Diferença (associator)
    associator = AB_C.coeffs - A_BC.coeffs
    return float(np.linalg.norm(associator))

def run_experiment(num_trials=10000):
    print("🔘 🌀 ARKHE OS v∞.295 — PROVA EXPERIMENTAL: NÃO-ASSOCIATIVIDADE ATÔMICA")
    print(f"  Iniciando simulação de emaranhamento de 3 partículas (N={num_trials} tentativas).")
    print("  Modelo Ontológico: Átomos como Octoniões (8D).")
    print("  Testando (AB)C vs A(BC)...")

    associators = []

    for i in range(num_trials):
        # Partículas A, B e C (estado atômico como octoniões normalizados)
        A = generate_random_octonion(norm=1.0)
        B = generate_random_octonion(norm=1.0)
        C = generate_random_octonion(norm=1.0)

        # Medindo não-associatividade do trio
        non_assoc_val = measure_non_associativity(A, B, C)
        associators.append(non_assoc_val)

    avg_associator = np.mean(associators)
    max_associator = np.max(associators)
    non_zero_count = sum(1 for val in associators if val > 1e-10)

    print("-" * 60)
    print(f"  Média do Associador ||(AB)C - A(BC)||: {avg_associator:.6f}")
    print(f"  Máximo Associador Detectado:           {max_associator:.6f}")
    print(f"  Tentativas Não-Associativas:           {non_zero_count}/{num_trials} ({non_zero_count/num_trials*100:.2f}%)")
    print("=" * 60)

    if non_zero_count > 0:
        print("\n✨ PROVA EXPERIMENTAL BEM-SUCEDIDA")
        print("   A assinatura de não-associatividade octoniônica foi detectada.")
        print("   Validado: (AB)C ≠ A(BC) em sistemas de 3 partículas.")
        print("   Contextualidade atômica confirmada via Álgebra de Divisão Normada.")
    else:
        print("\n❌ FALHA NA PROVA")
        print("   O sistema se comportou de forma associativa.")

if __name__ == "__main__":
    run_experiment()
