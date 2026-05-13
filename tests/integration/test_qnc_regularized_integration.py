#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_qnc_regularized_integration.py — Teste de integração: QNC Regularizado Φ_C
Valida convergência SIGHA + regularização Φ_C no QNC.
"""

import numpy as np
import pytest

from arkhe.layers.sigha_core import FisherBuresManifold, NaturalGradientFlow


def test_fisher_bures_distance():
    """Testa distância de Bures entre estados."""
    dim = 8
    manifold = FisherBuresManifold(dim)

    rho1 = np.eye(dim, dtype=complex) / dim
    rho2 = np.zeros((dim, dim), dtype=complex)
    rho2[0, 0] = 1.0

    d = manifold.bures_distance(rho1, rho2)
    assert np.isfinite(d)
    assert d > 0

    d_self = manifold.bures_distance(rho1, rho1)
    assert abs(d_self) < 1e-10
    print(f"✅ Bures distance: {d:.4f}")


def test_natural_gradient_preserves_trace():
    """Testa que gradiente natural preserva traço unitário."""
    dim = 8
    manifold = FisherBuresManifold(dim)
    flow = NaturalGradientFlow(manifold)

    rho = np.eye(dim, dtype=complex) / dim
    grad = rho - np.eye(dim, dtype=complex) / dim
    rho_new = flow.step(rho, grad, lr=0.1)

    assert abs(np.trace(rho_new) - 1.0) < 1e-10
    assert np.allclose(rho_new, rho_new.conj().T, atol=1e-10)
    print("✅ Natural gradient preserves trace")


def test_phi_c_convergence():
    """Testa convergência de Φ_C para estado puro."""
    dim = 16
    manifold = FisherBuresManifold(dim)
    flow = NaturalGradientFlow(manifold)

    psi = np.zeros(dim, dtype=complex)
    psi[0] = 1.0
    rho_target = np.outer(psi, psi.conj())

    rng = np.random.RandomState(42)
    rho = rng.randn(dim, dim) + 1j * rng.randn(dim, dim)
    rho = rho @ rho.conj().T
    rho /= np.trace(rho)

    initial_phi_c = 1 - manifold.bures_distance(rho, rho_target)

    for i in range(100):
        grad = rho - rho_target
        rho = flow.step(rho, grad, lr=0.05)

    final_phi_c = 1 - manifold.bures_distance(rho, rho_target)

    assert final_phi_c > initial_phi_c
    assert final_phi_c > 0.85
    print(f"✅ Φ_C convergence: {initial_phi_c:.4f} → {final_phi_c:.6f}")


def test_c_theorem_monotonicity():
    """Testa monotonicidade do c-teorema."""
    dim = 8
    manifold = FisherBuresManifold(dim)
    flow = NaturalGradientFlow(manifold)

    psi = np.zeros(dim, dtype=complex)
    psi[0] = 1.0
    rho_target = np.outer(psi, psi.conj())

    rng = np.random.RandomState(7)
    rho = rng.randn(dim, dim) + 1j * rng.randn(dim, dim)
    rho = rho @ rho.conj().T
    rho /= np.trace(rho)

    rhos = [rho]
    for i in range(50):
        grad = rho - rho_target
        rho = flow.step(rho, grad, lr=0.05)
        rhos.append(rho)

    c_vals = flow.c_theorem(rhos)
    valid_c = [c for c in c_vals if not np.isnan(c)]

    for i in range(1, len(valid_c)):
        assert valid_c[i] <= valid_c[i-1] + 1e-6

    assert valid_c[-1] < valid_c[0]
    print("✅ c-theorem monotonicity passed")


def test_canonical_seal():
    """Testa geração de selo canônico."""
    import hashlib, json
    seal_data = {
        "simulation": "SIGHA_Test",
        "final_phi_c": 0.999,
        "steps": 100,
        "dim": 8,
    }
    seal = hashlib.sha3_256(json.dumps(seal_data, sort_keys=True, default=str).encode()).hexdigest()[:16]
    assert len(seal) == 16
    print(f"✅ Canonical seal: {seal}")


def test_qnc_regularized_integration():
    """Teste de integração: SIGHA Φ_C → QNC Regularizado."""
    dim = 8
    manifold = FisherBuresManifold(dim)
    flow = NaturalGradientFlow(manifold)

    # 1. Converge Φ_C via SIGHA
    psi = np.zeros(dim, dtype=complex)
    psi[0] = 1.0
    rho_target = np.outer(psi, psi.conj())

    rng = np.random.RandomState(99)
    rho = rng.randn(dim, dim) + 1j * rng.randn(dim, dim)
    rho = rho @ rho.conj().T
    rho /= np.trace(rho)

    for i in range(50):
        grad = rho - rho_target
        rho = flow.step(rho, grad, lr=0.05)

    phi_c_final = 1 - manifold.bures_distance(rho, rho_target)

    # 2. Usa Φ_C como regularizador no QNC
    # Simula peso do classificador sendo regularizado por Φ_C
    weight = np.eye(dim, dtype=complex) / dim
    lambda_phi = 20.0

    for i in range(20):
        # Gradiente de classificação simulado
        class_grad = weight - np.eye(dim, dtype=complex) / dim
        # Regularização Φ_C
        phi_grad = lambda_phi * (weight - rho)
        total_grad = class_grad + phi_grad
        weight = flow.step(weight, total_grad, lr=0.05)

    # Peso deve estar mais próximo de rho (alta coerência) que do estado misto
    dist_to_rho = manifold.bures_distance(weight, rho)
    dist_to_mixed = manifold.bures_distance(weight, np.eye(dim, dtype=complex) / dim)

    assert phi_c_final > 0.70
    assert dist_to_rho < dist_to_mixed  # Regularização puxa para coerência

    print(f"\n🌀🧠 Integração SIGHA Φ_C → QNC Regularizado:")
    print(f"   Φ_C convergido: {phi_c_final:.6f}")
    print(f"   Distância ao estado coerente: {dist_to_rho:.4f}")
    print(f"   Distância ao estado misto: {dist_to_mixed:.4f}")
    print("✅ QNC regularized integration passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
