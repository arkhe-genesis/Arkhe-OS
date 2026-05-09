"""
GeodesicRouter: Roteamento via distância geodésica d_g(x,μ)² = (x-μ)^T g⁻¹ (x-μ).
Usa decomposição de Cholesky para inversão estável da métrica.
Compatível com PyTorch/XLA para TPU.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict

class GeodesicRouterRiemannian(nn.Module):
    """
    Roteamento de tokens para especialistas via métrica Riemanniana.
    Cada expert e tem centróide μ_e ∈ ℂ; distância: d_g(x,μ)² = (x-μ)^T g⁻¹ (x-μ).
    """

    def __init__(
        self,
        input_dim: int,
        num_experts: int,
        manifold_dim: int = 4,
        top_k: int = 8,
        temperature: float = 1.0,
        use_learned_metric: bool = True
    ):
        super().__init__()
        self.num_experts = num_experts
        self.manifold_dim = manifold_dim
        self.top_k = top_k
        self.temperature = temperature

        # Centróides dos experts no manifold
        self.expert_centroids = nn.Parameter(
            torch.randn(num_experts, manifold_dim) * 0.02
        )

        # Projeção do embedding para o manifold
        self.token_to_manifold = nn.Linear(input_dim, manifold_dim)

        # Métrica Riemanniana aprendida: g = L L^T
        if use_learned_metric:
            self.L_metric = nn.Parameter(
                torch.eye(manifold_dim) + torch.randn(manifold_dim, manifold_dim) * 0.01
            )
        else:
            self.register_buffer('L_metric', torch.eye(manifold_dim))

        # Gate network para pesos dos experts selecionados
        self.gate_net = nn.Sequential(
            nn.Linear(manifold_dim + input_dim + top_k, 64),
            nn.ReLU(),
            nn.Linear(64, top_k)
        )

    def _compute_metric_inverse(self) -> torch.Tensor:
        """Calcula g⁻¹ via Cholesky (estável numericamente)."""
        L = torch.tril(self.L_metric)
        g = L @ L.T + 1e-6 * torch.eye(self.manifold_dim, device=L.device)
        # g⁻¹ = (L⁻¹)^T L⁻¹
        L_inv = torch.linalg.solve_triangular(L, torch.eye(self.manifold_dim, device=L.device),
                                             upper=False)
        return L_inv.T @ L_inv

    def _geodesic_distance_squared(
        self,
        x: torch.Tensor,  # [batch, seq, manifold_dim]
        mu: torch.Tensor,  # [manifold_dim]
        g_inv: torch.Tensor  # [manifold_dim, manifold_dim]
    ) -> torch.Tensor:
        """
        Calcula d_g(x, μ)² = (x - μ)^T g⁻¹ (x - μ).
        Retorna tensor [batch, seq].
        """
        diff = x - mu.unsqueeze(0).unsqueeze(0)  # [batch, seq, dim]
        # d² = diff^T g⁻¹ diff (soma sobre dimensão do manifold)
        return torch.einsum('...i,ij,...j->...', diff, g_inv, diff)

    def forward(
        self,
        token_embeddings: torch.Tensor,  # [batch, seq_len, input_dim]
        metric: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict]:
        """
        Args:
            token_embeddings: [batch, seq_len, input_dim]
            metric: métrica g pré-computada (opcional)

        Returns:
            - expert_weights: [batch, seq_len, top_k] pesos normalizados
            - expert_indices: [batch, seq_len, top_k] índices dos experts
            - meta dict com distâncias, métrica usada, etc.
        """
        batch, seq_len, _ = token_embeddings.shape

        # Obter métrica e sua inversa
        if metric is None:
            g_inv = self._compute_metric_inverse()
        else:
            # Inverter métrica fornecida
            g_inv = torch.linalg.inv(metric + 1e-8 * torch.eye(self.manifold_dim, device=metric.device))

        # Mapear tokens para o manifold
        token_manifold = self.token_to_manifold(token_embeddings)  # [batch, seq, dim]

        # Calcular distâncias geodésicas a todos os experts
        distances = torch.stack([
            self._geodesic_distance_squared(token_manifold, self.expert_centroids[e], g_inv)
            for e in range(self.num_experts)
        ], dim=-1)  # [batch, seq, num_experts]

        # Converter distâncias em scores (menor distância = maior afinidade)
        scores = -distances / self.temperature

        # Selecionar top-k experts por score
        topk_scores, topk_indices = torch.topk(scores, self.top_k, dim=-1)  # [batch, seq, top_k]

        # Calcular pesos via gate network (inclui embedding original + distâncias)
        gate_input = torch.cat([
            token_embeddings,  # [batch, seq, input_dim]
            token_manifold,    # [batch, seq, manifold_dim]
            topk_scores        # [batch, seq, top_k]
        ], dim=-1)

        expert_weights = self.gate_net(gate_input)  # [batch, seq, top_k]
        expert_weights = F.softmax(expert_weights, dim=-1)

        metadata = {
            'geodesic_distances': torch.gather(
                distances, dim=-1,
                index=topk_indices
            ),  # distâncias dos experts selecionados
            'expert_indices': topk_indices,
            'metric_used': metric.detach().clone() if metric is not None else None,
            'g_inv_diagonal': torch.diag(g_inv)  # para debug
        }

        return expert_weights, topk_indices, metadata

    def to_xla_device(self, device=None):
        """Converte módulo para dispositivo XLA (TPU)."""
        try:
            import torch_xla.core.xla_model as xm
            if device is None:
                device = xm.xla_device()
            return self.to(device)
        except ImportError:
            return self
