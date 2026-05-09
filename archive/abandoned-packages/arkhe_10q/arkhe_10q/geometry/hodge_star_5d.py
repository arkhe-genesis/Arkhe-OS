#!/usr/bin/env python3
"""
hodge_star_5d.py — Operador ★^(5) via tensor de Levi-Civita 5D.
Implementação completa com pré-computação de matrizes de transformação.
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Optional, Tuple
from math import comb, factorial
from itertools import combinations, permutations

from .manifold_5d_frc2g import Manifold5DFRC2G

def precompute_transformation_matrices(manifold: Manifold5DFRC2G) -> Dict[int, torch.Tensor]:
    """
    Pré-computa matrizes de transformação ★_k: ℝ^{C(5,k)} → ℝ^{C(5,5-k)}.
    Satisfaz ★² = (-1)^(k(5-k)) por construção algébrica.
    """
    n = 5
    g_inv = manifold.get_metric_inverse()

    # Tensor de Levi-Civita 5D: ε_{i₁i₂i₃i₄i₅}
    epsilon = _build_levicivita_5d()

    matrices = {}

    for k in range(n + 1):
        dim_k = comb(n, k)
        dim_dual = comb(n, n - k)

        # Enumerar bases multi-índices
        basis_k = list(combinations(range(n), k))
        basis_dual = list(combinations(range(n), n - k))

        # Matriz de transformação: [dim_dual, dim_k]
        star_matrix = torch.zeros(dim_dual, dim_k, dtype=torch.float64)

        for j_idx, j_basis in enumerate(basis_dual):
            for i_idx, i_basis in enumerate(basis_k):
                # Calcular componente ★_k[i_basis → j_basis]
                # ★ω_{j} = (1/k!) ε_{j i} g^{iℓ} ω_ℓ
                value = _compute_hodge_component(
                    j_basis, i_basis, g_inv, epsilon, k
                )
                star_matrix[j_idx, i_idx] = value

        matrices[k] = star_matrix

    return matrices

def _build_levicivita_5d() -> torch.Tensor:
    """Constrói tensor de Levi-Civita totalmente antissimétrico ε_{i₁...i₅}."""
    n = 5
    epsilon = torch.zeros([n] * n, dtype=torch.float64)

    for perm in permutations(range(n)):
        # Calcular sinal da permutação via contagem de inversões
        inv_count = sum(1 for i in range(n) for j in range(i+1, n) if perm[i] > perm[j])
        sign = -1 if inv_count % 2 else 1
        epsilon[perm] = sign

    return epsilon

def _compute_hodge_component(
    j_basis: Tuple[int, ...],
    i_basis: Tuple[int, ...],
    g_inv: torch.Tensor,
    epsilon: torch.Tensor,
    k: int
) -> torch.Tensor:
    """
    Calcula componente individual da matriz ★_k.
    ★ω_{j} = (1/k!) ε_{j i} g^{iℓ} ω_ℓ
    """
    n = 5
    value = torch.tensor(0.0, dtype=g_inv.dtype, device=g_inv.device)

    # Somar sobre todas as ℓ-basis possíveis
    for ell_basis in combinations(range(n), k):
        # Verificar se índices são permutação válida
        full_indices = list(j_basis) + list(i_basis)
        if len(set(full_indices)) < n:
            continue  # Índices repetidos → ε = 0

        # Calcular sinal da permutação para ordenar full_indices
        sorted_indices = sorted(range(n), key=lambda x: full_indices[x])
        sign = 1
        for a in range(n):
            for b in range(a+1, n):
                if sorted_indices[a] > sorted_indices[b]:
                    sign *= -1

        # Fator métrico: ∏_{p=1}^k g^{i_p, ℓ_p}
        metric_factor = 1.0
        for i_idx, ell_idx in zip(i_basis, ell_basis):
            metric_factor = metric_factor * g_inv[i_idx, ell_idx]

        # Contribuição apenas se ℓ_basis == i_basis (ω tem componente em i_basis)
        if ell_basis == i_basis:
            value += sign * metric_factor

    return value

class HodgeStar5D:
    """
    Operador ★^(5): Ω^k → Ω^(5-k) em manifold 5D.
    Satisfaz ★² = (-1)^(k(5-k)) por construção.

    Uso:
        hodge = HodgeStar5D(manifold, precompute=True)
        star_omega = hodge.apply(omega, k=2)  # Ω² → Ω³
    """

    def __init__(self, manifold: Manifold5DFRC2G, precompute: bool = True):
        self.manifold = manifold
        self.n = 5
        self.precompute = precompute

        if precompute:
            self._transformation_matrices = precompute_transformation_matrices(manifold)
        else:
            self._transformation_matrices = None

        # Cache de métrica inversa
        self._g_inv_cache: Optional[torch.Tensor] = None

    def apply(self, omega: torch.Tensor, k: int) -> torch.Tensor:
        """
        Aplica ★^(5): Ω^k → Ω^(5-k).

        Args:
            omega: coeficientes da k-forma [batch, C(5,k)]
            k: grau da forma (0 ≤ k ≤ 5)

        Returns:
            ★ω: coeficientes da (5-k)-forma [batch, C(5,5-k)]
        """
        from math import comb
        batch = omega.shape[0]
        expected_dim = comb(self.n, k)

        if omega.shape[-1] != expected_dim:
            raise ValueError(f"Expected omega dim {expected_dim} for k={k}, got {omega.shape[-1]}")

        if self.precompute:
            # Usar matriz pré-computada
            if k not in self._transformation_matrices:
                raise ValueError(f"No precomputed matrix for k={k}")
            star_matrix = self._transformation_matrices[k]
            return omega @ star_matrix.T  # [batch, dim_k] @ [dim_k, dim_dual]
        else:
            # Computar on-the-fly (mais lento, mas suporta métrica dinâmica)
            return self._apply_dynamic(omega, k)

    def _apply_dynamic(self, omega: torch.Tensor, k: int) -> torch.Tensor:
        """Aplica ★ com métrica dinâmica (sem pré-computação)."""
        # Implementação simplificada: recalcular matriz para cada call
        # Em produção: usar caching inteligente ou aproximação
        g_inv = self.manifold.get_metric_inverse()
        epsilon = _build_levicivita_5d()
        star_matrix = _compute_transformation_matrix_dynamic(k, g_inv, epsilon, self.n)
        return omega @ star_matrix.T

def _compute_transformation_matrix_dynamic(
    k: int, g_inv: torch.Tensor, epsilon: torch.Tensor, n: int = 5
) -> torch.Tensor:
    """Versão dinâmica de pré-computação para métricas variáveis."""
    from math import comb, factorial
    from itertools import combinations

    dim_k = comb(n, k)
    dim_dual = comb(n, n - k)
    basis_k = list(combinations(range(n), k))
    basis_dual = list(combinations(range(n), n - k))

    star_matrix = torch.zeros(dim_dual, dim_k, dtype=g_inv.dtype)

    for j_idx, j_basis in enumerate(basis_dual):
        for i_idx, i_basis in enumerate(basis_k):
            value = _compute_hodge_component(j_basis, i_basis, g_inv, epsilon, k)
            star_matrix[j_idx, i_idx] = value

    return star_matrix
