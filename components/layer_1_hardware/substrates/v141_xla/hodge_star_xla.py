"""
HodgeStarLeviCivita otimizado para XLA/TPU.
Estratégias:
1. Substituir loops Python por operações vetoriais/einsum
2. Pré-computar ★_k como tensor constante (não reconstruir por forward)
3. Usar jax.lax.custom_call para contração de Levi-Civita se necessário
4. Evitar .item(), numpy, ou operações não-diferenciáveis no grafo
"""

import torch
from typing import Dict, Optional
import torch.nn.functional as F
import torch.nn as nn
from layer_1_hardware.substrates.v141.hodge_star_levicivita import HodgeStarLeviCivita

class HodgeStarLeviCivitaXLA(HodgeStarLeviCivita):
    """Versão XLA-optimized do operador ★_g."""

    def __init__(self, manifold_dim: int = 4, learnable_metric: bool = True):
        super().__init__(manifold_dim, learnable_metric)
        # Pré-computar matrizes ★_k como buffers (não parâmetros aprendíveis)
        self._precompute_star_matrices()

    def _precompute_star_matrices(self):
        """Pré-computa ★_k para cada k como tensor constante."""
        g_inv = self.metric_inverse().detach()  # sem gradiente para pré-computação
        eps = self.epsilon.get()

        self.star_matrices = {}
        for k in range(self.n + 1):
            if k <= self.n:
                self.star_matrices[k] = self._build_star_matrix(k, g_inv, eps).detach()

    def forward(self, omega: torch.Tensor, k: int) -> torch.Tensor:
        """Forward XLA-compatible: usa matriz pré-computada + einsum."""
        if k not in self.star_matrices:
            raise ValueError(f"★_{k} not precomputed for dim={self.n}")

        # Aplicar transformação linear via matmul (XLA-friendly)
        star_matrix = self.star_matrices[k]
        return torch.matmul(omega, star_matrix.T)  # [batch, C(n,k)] @ [C(n,k), C(n,n-k)]

    def metric_inverse_xla(self) -> torch.Tensor:
        """Versão XLA-stable de g⁻¹ via Cholesky."""
        g = self.metric()
        # Cholesky é suportado em XLA; usar solve_triangular para estabilidade
        L = torch.linalg.cholesky(g)
        # Resolver L @ X = I para obter L⁻¹
        I = torch.eye(self.n, device=g.device)
        L_inv = torch.linalg.solve_triangular(L, I, upper=False)
        return L_inv.T @ L_inv

    @staticmethod
    def xla_mark_step():
        """Força sincronização em TPU (útil para debug de grafos)."""
        try:
            import torch_xla.core.xla_model as xm
            xm.mark_step()
        except ImportError:
            pass
