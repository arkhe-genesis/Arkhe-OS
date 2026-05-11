import torch
import torch.nn as nn
from typing import Dict, Tuple, Optional

class GeodesicRouter(nn.Module):
    """
    Roteamento MoE baseado em distância geodésica no manifold de especialistas.

    Cada expert e é representado por um ponto μ_e no manifold de coerência C.
    Para um token com embedding x, o expert selecionado é:
    e* = argmin_e d_g(x, μ_e)

    Implementa Voronoi geodésico com métrica Riemanniana aprendida.
    """

    def __init__(
        self,
        num_experts: int,
        d_model: int,
        manifold_dim: int = 4,
        top_k: int = 8,
        use_learned_metric: bool = True
    ):
        super().__init__()
        self.num_experts = num_experts
        self.d_model = d_model
        self.manifold_dim = manifold_dim
        self.top_k = top_k

        # Centróides dos experts no manifold (pontos em C)
        self.expert_centroids = nn.Parameter(
            torch.randn(num_experts, manifold_dim) * 0.1
        )

        # Métrica Riemanniana global (compartilhada com TokenToFormLayer)
        if use_learned_metric:
            self.L_metric = nn.Parameter(torch.eye(manifold_dim) + torch.randn(manifold_dim, manifold_dim) * 0.01)
        else:
            self.register_buffer('L_metric', torch.eye(manifold_dim))

        # Projeção do embedding do token para o manifold
        self.token_to_manifold = nn.Linear(d_model, manifold_dim)

        # Gate network para pesos dos experts selecionados (após seleção geodésica)
        self.gate_net = nn.Sequential(
            nn.Linear(manifold_dim + d_model + top_k, 64),
            nn.ReLU(),
            nn.Linear(64, top_k)
        )

    def forward(
        self,
        token_embeddings: torch.Tensor,
        metric: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict]:
        """
        Args:
            token_embeddings: [batch, seq_len, d_model]
            metric: métrica Riemanniana [manifold_dim, manifold_dim] (opcional)

        Returns:
            - selected_experts: [batch, seq_len, top_k] índices dos experts
            - expert_weights: [batch, seq_len, top_k] pesos normalizados
            - metadata: dict com distâncias geodésicas, etc.
        """
        batch, seq_len, _ = token_embeddings.shape

        # Usar métrica fornecida ou calcular a partir de L_metric
        if metric is None:
            L = torch.tril(self.L_metric)
            metric = L @ L.T

        # Mapear tokens para o manifold de coerência
        token_manifold_coords = self.token_to_manifold(token_embeddings)  # [batch, seq_len, manifold_dim]

        # Calcular distâncias geodésicas aproximadas (usando métrica local)
        # d_g(x, μ)² = (x - μ)^T g^{-1} (x - μ)
        g_inv = torch.linalg.inv(metric + 1e-8 * torch.eye(self.manifold_dim, device=metric.device))

        # Calcular distâncias para todos os experts
        distances = []
        for e in range(self.num_experts):
            mu_e = self.expert_centroids[e]  # [manifold_dim]
            diff = token_manifold_coords - mu_e.unsqueeze(0).unsqueeze(0)  # [batch, seq_len, manifold_dim]
            # d² = diff^T g^{-1} diff (soma sobre dimensão do manifold)
            d_sq = torch.einsum('...i,ij,...j->...', diff, g_inv, diff)  # [batch, seq_len]
            distances.append(d_sq)

        distances = torch.stack(distances, dim=-1)  # [batch, seq_len, num_experts]

        # Selecionar top_k experts por menor distância geodésica
        selected_distances, selected_indices = torch.topk(
            distances, k=self.top_k, dim=-1, largest=False
        )  # [batch, seq_len, top_k]

        # Calcular pesos dos experts selecionados via gate network
        # Concatenar embedding original + coordenadas no manifold + distâncias
        gate_input = torch.cat([
            token_embeddings,  # [batch, seq_len, d_model]
            token_manifold_coords,  # [batch, seq_len, manifold_dim]
            selected_distances  # [batch, seq_len, top_k]
        ], dim=-1)

        expert_weights = self.gate_net(gate_input)  # [batch, seq_len, top_k]
        expert_weights = torch.softmax(expert_weights, dim=-1)  # normalizar

        metadata = {
            'geodesic_distances': selected_distances,
            'selected_experts': selected_indices,
            'metric_used': metric.detach().clone()
        }

        return selected_indices, expert_weights, metadata
