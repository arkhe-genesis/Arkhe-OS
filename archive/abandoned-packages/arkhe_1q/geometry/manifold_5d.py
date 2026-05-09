# arkhe_1q/geometry/manifold_5d.py
import torch
import torch.nn as nn
from typing import Optional

class Manifold5D:
    """
    Manifold Riemanniano 5-dimensional com fibrado de escala.
    Métrica: g_AB = diag(g_μν, λ⁻²) com λ fator de escala dinâmico.
    """

    def __init__(self, base_dim: int = 4, scale_fiber_dim: int = 1,
                 learnable_metric: bool = True, torsion_strength: float = 2.04):
        self.base_dim = base_dim
        self.total_dim = base_dim + scale_fiber_dim
        self.learnable_metric = learnable_metric

        # Métrica base 4D parametrizada via Cholesky
        if learnable_metric:
            self.L_base = nn.Parameter(torch.eye(base_dim) * 0.1 +
                                      torch.randn(base_dim, base_dim) * 0.01)
        else:
            # We can't register a buffer unless it's an nn.Module, but let's keep the API
            self.L_base = torch.eye(base_dim)

        # Fator de escala λ (aprendível, positivo por construção)
        self.log_lambda = nn.Parameter(torch.tensor(0.0))  # λ = exp(log_lambda)

        # Tensor de torção para acoplamento escala-geometria
        self.torsion_coupling = nn.Parameter(torch.tensor(torsion_strength))

        # Cache de métrica inversa
        self._metric_cache: Optional[torch.Tensor] = None
        self._inv_cache: Optional[torch.Tensor] = None

    def get_metric(self) -> torch.Tensor:
        """Retorna métrica 5D completa: g_AB = diag(g_μν, λ⁻²)."""
        if self._metric_cache is not None:
            return self._metric_cache

        # Métrica base 4D via Cholesky
        L = torch.tril(self.L_base)
        g_base = L @ L.T + 1e-8 * torch.eye(self.base_dim, device=L.device)

        # Fator de escala
        lambda_val = torch.exp(self.log_lambda)
        scale_component = torch.tensor([[1.0 / (lambda_val**2 + 1e-8)]],
                                      device=g_base.device)

        # Métrica block-diagonal 5D
        g_5d = torch.block_diag(g_base, scale_component)

        self._metric_cache = g_5d.detach() if not self.learnable_metric else g_5d
        return g_5d

    def get_metric_inverse(self) -> torch.Tensor:
        """Retorna g^AB via inversão block-diagonal eficiente."""
        if self._inv_cache is not None:
            return self._inv_cache

        g = self.get_metric()

        # Inversão block-diagonal: (block_diag(A, b))⁻¹ = block_diag(A⁻¹, 1/b)
        g_base = g[:self.base_dim, :self.base_dim]
        scale_inv = 1.0 / g[self.base_dim:, self.base_dim:]

        # Inverter base 4D via Cholesky
        L = torch.linalg.cholesky(g_base)
        L_inv = torch.linalg.solve_triangular(L, torch.eye(self.base_dim, device=g.device),
                                             upper=False)
        g_base_inv = L_inv.T @ L_inv

        # Montar inversa 5D
        g_inv = torch.block_diag(g_base_inv, scale_inv)

        self._inv_cache = g_inv.detach() if not self.learnable_metric else g_inv
        return g_inv

    def set_scale_factor(self, lambda_val: float):
        """Define fator de escala λ explicitamente."""
        with torch.no_grad():
            self.log_lambda.copy_(torch.log(torch.tensor(lambda_val + 1e-8)))
        self._invalidate_caches()

    def get_scale_factor(self) -> float:
        """Retorna fator de escala atual λ."""
        return torch.exp(self.log_lambda).item()

    def hodge_star_5d(self, omega: torch.Tensor, k: int) -> torch.Tensor:
        """
        Aplica operador de Hodge ★^(5): Ω^k → Ω^(5-k) em 5D.
        Satisfaz ★² = (-1)^(k(5-k)) por construção.
        """
        # Em produção: implementar via tensor de Levi-Civita 5D + métrica
        # Simplificação: usar matriz de transformação pré-computada
        sign = (-1)**(k * (5 - k))

        # Para k=2 em 5D: dim(Ω²) = C(5,2)=10, dim(Ω³)=C(5,3)=10
        # Transformação linear que preserva norma com sinal correto
        if k == 2:
            # ★: Ω² → Ω³, mesma dimensão
            return sign * omega  # simplificação ortogonal
        else:
            # Implementação completa requer pré-computação de matriz ★_k
            raise NotImplementedError("Full 5D Hodge star requires precomputed transformation matrices")

    def _invalidate_caches(self):
        """Invalida caches de métrica após mudança de parâmetros."""
        self._metric_cache = None
        self._inv_cache = None
