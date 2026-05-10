#!/usr/bin/env python3
"""
manifold_5d_xla.py — Manifold 5D otimizado para XLA/TPU v6.
Converte operações para primitivas XLA compatíveis com geometria 5D.

ARKHE 10Q Phase 0 — Milestone 1
"""

import torch
import torch.nn as nn
try:
    import torch_xla.core.xla_model as xm
    XLA_AVAILABLE = True
except ImportError:
    XLA_AVAILABLE = False
from typing import Dict, Optional, Tuple, List
from math import comb

class Manifold5DXLA(nn.Module):
    """
    Manifold 5D com operações XLA-native para TPU v6.
    Métrica: g_5D = block_diag(g_4D, λ⁻²) via Cholesky estável.
    """

    def __init__(self, base_dim: int = 4, learnable: bool = True,
                 xla_compatible: bool = True):
        super().__init__()
        self.base_dim = base_dim
        self.total_dim = base_dim + 1  # +1 para dimensão de escala λ
        self.xla_compatible = xla_compatible

        # Métrica base 4D via Cholesky (XLA-stable)
        if learnable:
            # Inicialização que evita NaN em XLA
            self.L_base = nn.Parameter(
                torch.eye(base_dim) * 0.5 + torch.randn(base_dim, base_dim) * 0.02
            )
        else:
            self.register_buffer('L_base', torch.eye(base_dim) * 0.5)

        # Fator de escala λ > 0 via exp(log_λ)
        self.log_lambda = nn.Parameter(torch.tensor(0.0))  # λ = exp(0) = 1.0 inicial

        # Cache de métrica (invalidado quando parâmetros mudam)
        self._metric_cache: Optional[torch.Tensor] = None
        self._inv_cache: Optional[torch.Tensor] = None
        self._volume_cache: Optional[float] = None

        # Constantes numéricas para estabilidade XLA
        self.eps = 1e-8
        self.max_lambda = 1e4
        self.min_lambda = 1e-4

    def get_metric(self) -> torch.Tensor:
        """Retorna métrica 5D: g_AB = block_diag(g_μν, λ⁻²)."""
        if self._metric_cache is not None and not self.training:
            return self._metric_cache

        # Métrica base 4D via Cholesky (XLA-compatible)
        L = torch.tril(self.L_base)  # Forçar triangular inferior
        g_base = L @ L.T + self.eps * torch.eye(self.base_dim, device=L.device)

        # Fator de escala λ (com clipping para estabilidade)
        lambda_val = torch.clamp(
            torch.exp(self.log_lambda),
            min=self.min_lambda,
            max=self.max_lambda
        )
        scale_component = torch.tensor(
            [[1.0 / (lambda_val**2 + self.eps)]],
            device=g_base.device,
            dtype=g_base.dtype
        )

        # Métrica block-diagonal 5D (XLA-friendly: sem loops Python)
        g_5d = torch.block_diag(g_base, scale_component)

        if not self.training:
            self._metric_cache = g_5d.detach()
        return g_5d

    def get_metric_inverse(self) -> torch.Tensor:
        """Retorna g^AB via inversão block-diagonal eficiente (XLA-stable)."""
        if self._inv_cache is not None and not self.training:
            return self._inv_cache

        g = self.get_metric()

        # Inversão block-diagonal: (block_diag(A, b))⁻¹ = block_diag(A⁻¹, 1/b)
        g_base = g[:self.base_dim, :self.base_dim]
        scale_inv = 1.0 / (g[self.base_dim:, self.base_dim:] + self.eps)

        # Inverter base 4D via Cholesky (mais estável que inverse() em XLA)
        L = torch.linalg.cholesky(g_base)
        I = torch.eye(self.base_dim, device=g.device, dtype=g.dtype)
        L_inv = torch.linalg.solve_triangular(L, I, upper=False)
        g_base_inv = L_inv.T @ L_inv

        # Montar inversa 5D
        g_inv = torch.block_diag(g_base_inv, scale_inv)

        if not self.training:
            self._inv_cache = g_inv.detach()
        return g_inv

    def get_volume_form(self) -> torch.Tensor:
        """Retorna forma de volume √|det(g)| (XLA-compatible)."""
        if self._volume_cache is not None and not self.training:
            return torch.tensor(self._volume_cache, device=self.L_base.device)

        # det(block_diag(A, b)) = det(A) * b
        L = torch.tril(self.L_base)
        det_g_base = torch.prod(torch.diag(L))**2  # det(LL^T) = (prod diag L)²
        lambda_val = torch.clamp(torch.exp(self.log_lambda), min=self.min_lambda, max=self.max_lambda)
        det_g_5d = det_g_base * (1.0 / lambda_val**2)

        volume = torch.sqrt(torch.abs(det_g_5d) + self.eps)

        if not self.training:
            self._volume_cache = volume.item()
        return volume

    def set_scale_factor(self, lambda_val: float):
        """Define fator de escala λ explicitamente (com validação)."""
        with torch.no_grad():
            safe_lambda = max(self.min_lambda, min(self.max_lambda, lambda_val))
            self.log_lambda.copy_(torch.log(torch.tensor(safe_lambda + self.eps)))
        self._invalidate_caches()

    def get_scale_factor(self) -> float:
        """Retorna fator de escala atual λ."""
        return torch.clamp(torch.exp(self.log_lambda), min=self.min_lambda, max=self.max_lambda).item()

    def _invalidate_caches(self):
        """Invalida caches após mudança de parâmetros."""
        self._metric_cache = None
        self._inv_cache = None
        self._volume_cache = None

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass: projeta x no manifold e retorna (x_proj, g(x)).
        Útil para camadas que precisam da métrica local.
        """
        # Normalização simples para manter x dentro do mercy gap [0.04, 0.10]
        x_norm = torch.norm(x, dim=-1, keepdim=True)
        x_proj = x / (x_norm + self.eps) * 0.07  # Projetar para raio 0.07

        # Retornar projeção + métrica no ponto
        return x_proj, self.get_metric()


class HodgeStar5DXLA:
    """
    Operador ★^(5): Ω^k → Ω^(5-k) otimizado para XLA.
    Usa matrizes de transformação pré-computadas para evitar loops em forward.
    """

    def __init__(self, manifold: Manifold5DXLA, precompute: bool = True):
        self.manifold = manifold
        self.n = 5
        self.precompute = precompute

        if precompute:
            # Pré-computar matrizes de transformação para cada k
            self._transformation_matrices = self._precompute_all_matrices()
        else:
            self._transformation_matrices = None

    def _precompute_all_matrices(self) -> Dict[int, torch.Tensor]:
        """Pré-computa ★_k para k=0..5 via Levi-Civita 5D."""
        from itertools import combinations, permutations
        from math import factorial

        n = 5
        g_inv = self.manifold.get_metric_inverse().detach()

        # Tensor de Levi-Civita 5D ε_{i₁i₂i₃i₄i₅}
        epsilon = torch.zeros([n]*n, dtype=torch.float64)
        for perm in permutations(range(n)):
            inv_count = sum(1 for i in range(n) for j in range(i+1, n) if perm[i] > perm[j])
            epsilon[perm] = -1 if inv_count % 2 else 1

        matrices = {}

        for k in range(n + 1):
            dim_k = comb(n, k)
            dim_dual = comb(n, n - k)
            basis_k = list(combinations(range(n), k))
            basis_dual = list(combinations(range(n), n - k))

            # Matriz ★_k: [dim_dual, dim_k]
            star_mat = torch.zeros(dim_dual, dim_k, dtype=torch.float64)

            for j_idx, j_basis in enumerate(basis_dual):
                for i_idx, i_basis in enumerate(basis_k):
                    # Calcular componente ★_k[i→j]
                    value = 0.0
                    for ell_basis in combinations(range(n), k):
                        full = list(j_basis) + list(i_basis)
                        if len(set(full)) < n:
                            continue
                        # Sinal da permutação
                        sorted_idx = sorted(range(n), key=lambda x: full[x])
                        sign = 1
                        for a in range(n):
                            for b in range(a+1, n):
                                if sorted_idx[a] > sorted_idx[b]:
                                    sign *= -1
                        # Fator métrico
                        metric_factor = 1.0
                        for i_p, ell_p in zip(i_basis, ell_basis):
                            metric_factor *= g_inv[i_p, ell_p].item()
                        if ell_basis == i_basis:
                            value += sign * metric_factor
                    star_mat[j_idx, i_idx] = value / factorial(k)

            matrices[k] = star_mat

        return matrices

    def apply(self, omega: torch.Tensor, k: int) -> torch.Tensor:
        """Aplica ★^(5): Ω^k → Ω^(5-k) via matriz pré-computada."""
        from math import comb
        batch = omega.shape[0]
        expected_dim = comb(self.n, k)

        if omega.shape[-1] != expected_dim:
            raise ValueError(f"Expected dim {expected_dim} for k={k}, got {omega.shape[-1]}")

        if self.precompute:
            if k not in self._transformation_matrices:
                raise ValueError(f"No precomputed matrix for k={k}")
            star_matrix = self._transformation_matrices[k].to(omega.device).to(omega.dtype)
            # Matmul é XLA-native e eficiente
            return omega @ star_matrix.T
        else:
            # Fallback dinâmico (mais lento, mas suporta métrica variável)
            return self._apply_dynamic(omega, k)

    def _apply_dynamic(self, omega: torch.Tensor, k: int) -> torch.Tensor:
        """Aplica ★ com métrica dinâmica (sem pré-computação)."""
        # Em produção: usar caching inteligente ou aproximação de baixa ordem
        raise NotImplementedError("Dynamic Hodge star requires optimized implementation")

    def verify_involution(self, k: int, tol: float = 1e-4) -> bool:
        """Verifica ★² = (-1)^(k(5-k)) · id para validação."""
        if not self.precompute:
            return False
        n = 5
        sign = (-1)**(k * (n - k))
        M_k = self._transformation_matrices[k]
        M_nk = self._transformation_matrices[n - k]
        involution = M_nk @ M_k
        expected = sign * torch.eye(M_k.shape[1], dtype=torch.float64)
        return torch.allclose(involution, expected, atol=tol)
