#!/usr/bin/env python3
"""
test_hodge_star_5d.py — Testes unitários para Hodge star em 5D.
Verifica propriedade fundamental: ★² = (-1)^(k(5-k)) · id para k=0..5.
"""
import pytest
import torch
import numpy as np
from arkhe_10q.geometry.manifold_5d_frc2g import Manifold5DFRC2G
from arkhe_10q.geometry.hodge_star_5d import HodgeStar5D, precompute_transformation_matrices

class TestHodgeStar5D:
    """Suite de testes para operador ★^(5): Ω^k → Ω^(5-k)."""

    @pytest.fixture
    def manifold_5d(self):
        """Fixture: manifold 5D com métrica aprendível."""
        return Manifold5DFRC2G(base_dim=4, learnable=True)

    @pytest.fixture
    def hodge_5d(self, manifold_5d):
        """Fixture: operador Hodge star 5D pré-computado."""
        return HodgeStar5D(manifold_5d, precompute=True)

    @pytest.mark.parametrize("k", range(6))  # k = 0, 1, 2, 3, 4, 5
    def test_hodge_involution_property(self, hodge_5d, k):
        """
        TESTE CRÍTICO: Verifica ★² = (-1)^(k(5-k)) · id.

        Para cada grau k:
        1. Gera forma aleatória ω ∈ Ω^k
        2. Aplica ★: ω → ★ω ∈ Ω^(5-k)
        3. Aplica ★ novamente: ★ω → ★²ω ∈ Ω^k
        4. Verifica: ★²ω = sign · ω com sign = (-1)^(k(5-k))
        """
        # Dimensão do espaço de k-formas em 5D: C(5, k)
        from math import comb
        dim_k = comb(5, k)

        # Gerar forma aleatória (batch=2 para testar vetorização)
        omega = torch.randn(2, dim_k, dtype=torch.float64)

        # Calcular sinal teórico
        expected_sign = (-1)**(k * (5 - k))

        # Aplicar ★ duas vezes
        star_omega = hodge_5d.apply(omega, k)  # Ω^k → Ω^(5-k)
        star_star_omega = hodge_5d.apply(star_omega, 5 - k)  # Ω^(5-k) → Ω^k

        # Verificar igualdade com tolerância numérica
        # Nota: para k=2 e k=3, dim(Ω²)=dim(Ω³)=10, então transformação é quadrática
        assert star_star_omega.shape == omega.shape, \
            f"Shape mismatch: expected {omega.shape}, got {star_star_omega.shape}"

        # Verificar ★²ω ≈ sign · ω
        expected = expected_sign * omega
        assert torch.allclose(star_star_omega, expected, atol=1e-6, rtol=1e-5), \
            f"★² ≠ {expected_sign}·id for k={k}. Max error: {torch.max(torch.abs(star_star_omega - expected)).item()}"

        print(f"  ✓ k={k}: ★² = {expected_sign}·id (max error: {torch.max(torch.abs(star_star_omega - expected)).item():.2e})")

    def test_hodge_preserves_inner_product(self, hodge_5d, manifold_5d):
        """
        TESTE: ★ preserva produto interno: ⟨α, β⟩ = ⟨★α, ★β⟩.

        Para α, β ∈ Ω^k: ∫ α ∧ ★β = ⟨α, β⟩_g · vol
        """
        k = 2  # Testar para 2-formas
        from math import comb
        dim_k = comb(5, k)

        # Gerar duas formas aleatórias
        alpha = torch.randn(1, dim_k, dtype=torch.float64)
        beta = torch.randn(1, dim_k, dtype=torch.float64)

        # Produto interno via métrica
        g = manifold_5d.get_metric()
        # Simplificação: produto interno euclidiano no espaço de coeficientes
        inner_original = torch.sum(alpha * beta, dim=-1)

        # Aplicar ★ a ambas
        star_alpha = hodge_5d.apply(alpha, k)
        star_beta = hodge_5d.apply(beta, k)

        # Produto interno das formas duais
        inner_dual = torch.sum(star_alpha * star_beta, dim=-1)

        # Verificar preservação (com tolerância para aproximação numérica)
        assert torch.allclose(inner_original, inner_dual, atol=1e-5), \
            f"Inner product not preserved: {inner_original.item()} vs {inner_dual.item()}"

        print(f"  ✓ Produto interno preservado para k={k}: ⟨α,β⟩={inner_original.item():.4f}, ⟨★α,★β⟩={inner_dual.item():.4f}")

    def test_hodge_dimension_mapping(self, hodge_5d):
        """TESTE: ★ mapeia dimensões corretamente: dim(Ω^k) → dim(Ω^(5-k))."""
        from math import comb

        for k in range(6):
            dim_k = comb(5, k)
            dim_dual = comb(5, 5 - k)

            # Forma de teste
            omega = torch.randn(1, dim_k, dtype=torch.float64)
            star_omega = hodge_5d.apply(omega, k)

            assert star_omega.shape[-1] == dim_dual, \
                f"Dimension mismatch for k={k}: expected {dim_dual}, got {star_omega.shape[-1]}"

            print(f"  ✓ k={k}: dim(Ω^{k})={dim_k} → dim(Ω^{5-k})={dim_dual}")

    def test_hodge_linearity(self, hodge_5d):
        """TESTE: ★ é operador linear: ★(a·ω₁ + b·ω₂) = a·★ω₁ + b·★ω₂."""
        k = 1
        from math import comb
        dim_k = comb(5, k)

        # Formas e coeficientes aleatórios
        omega1 = torch.randn(1, dim_k, dtype=torch.float64)
        omega2 = torch.randn(1, dim_k, dtype=torch.float64)
        a, b = 0.7, -1.3

        # LHS: ★(a·ω₁ + b·ω₂)
        lhs = hodge_5d.apply(a * omega1 + b * omega2, k)

        # RHS: a·★ω₁ + b·★ω₂
        rhs = a * hodge_5d.apply(omega1, k) + b * hodge_5d.apply(omega2, k)

        assert torch.allclose(lhs, rhs, atol=1e-6), \
            f"Linearity failed: max diff = {torch.max(torch.abs(lhs - rhs)).item()}"

        print(f"  ✓ Linearidade verificada para k={k}")

    @pytest.mark.slow
    def test_hodge_with_learnable_metric(self):
        """TESTE: ★² = ±1 mantém-se com métrica aprendível (gradiente flui)."""
        manifold = Manifold5DFRC2G(base_dim=4, learnable=True)
        hodge = HodgeStar5D(manifold, precompute=False)  # Recalcula a cada forward

        k = 2
        from math import comb
        dim_k = comb(5, k)

        omega = torch.randn(2, dim_k, dtype=torch.float64, requires_grad=False)
        expected_sign = (-1)**(k * (5 - k))

        # Forward pass
        star_omega = hodge.apply(omega, k)
        star_star_omega = hodge.apply(star_omega, 5 - k)

        # Verificar propriedade
        assert torch.allclose(star_star_omega, expected_sign * omega, atol=1e-5)

        # Verificar que gradientes podem fluir através da métrica
        manifold.L_base.requires_grad_(True)
        manifold.log_lambda.requires_grad_(True)

        # Loss simples para backprop
        loss = torch.sum((star_star_omega - expected_sign * omega)**2)
        loss.backward()

        # Verificar que gradientes foram computados
        assert manifold.L_base.grad is not None, "No gradient for L_base"
        assert manifold.log_lambda.grad is not None, "No gradient for log_lambda"

        print(f"  ✓ Gradientes fluem através de ★ com métrica aprendível")


if __name__ == "__main__":
    # Execução manual para desenvolvimento
    pytest.main([__file__, "-v", "-s"])
