"""
GeodesicRouter: Roteamento de tokens para especialistas via distância de Fisher‑Rao
no manifold de coerência. Compatível com PyTorch/XLA para TPU.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class GeodesicRouter(nn.Module):
    def __init__(self, input_dim: int, num_experts: int, manifold_dim: int = 4,
                 top_k: int = 8, temperature: float = 1.0):
        super().__init__()
        self.num_experts = num_experts
        self.top_k = top_k
        self.temp = temperature
        self.manifold_dim = manifold_dim

        # Cada expert tem um centróide μ_e no manifold (representado como 1‑forma)
        self.expert_centroids = nn.Parameter(
            torch.randn(num_experts, manifold_dim) * 0.02
        )
        # Projeção do token para o manifold (1‑forma equivalente)
        self.token_projector = nn.Linear(input_dim, manifold_dim)

    def geodesic_distance(self, token_repr: torch.Tensor,
                         expert_repr: torch.Tensor) -> torch.Tensor:
        """
        Distância de Fisher‑Rao aproximada entre token e centróide.
        Aqui usamos a distância na esfera (normalização unitária) como proxy.
        """
        # Normalizar para a esfera unitária (restrição ‖ω‖=1)
        token_norm = F.normalize(token_repr, dim=-1)
        expert_norm = F.normalize(expert_repr, dim=-1)
        # Ângulo geodésico
        cos_angle = torch.matmul(token_norm, expert_norm.T)
        cos_angle = torch.clamp(cos_angle, -0.9999, 0.9999)
        angle = torch.acos(cos_angle)
        return angle

    def forward(self, token_states: torch.Tensor):
        """
        Entrada: (batch, input_dim)
        Saída: (router_probs, expert_indices)
        """
        # Projetar tokens para o manifold
        token_1form = self.token_projector(token_states)  # (batch, dim_man)

        # Distância geodésica a cada expert
        dist = self.geodesic_distance(token_1form, self.expert_centroids)  # (batch, num_experts)
        # Converter em score: quanto menor a distância, maior a afinidade
        scores = -dist / self.temp
        # Selecção top‑k suave (via Gumbel ou softmax + máscara)
        topk_vals, topk_idx = torch.topk(scores, self.top_k, dim=-1)
        weights = F.softmax(topk_vals, dim=-1)  # pesos entre os escolhidos

        return weights, topk_idx

    # Métodos auxiliares para TPU
    def to_xla(self):
        try:
            import torch_xla.core.xla_model as xm
            return xm.send_cpu_data_to_device(self, xm.xla_device())
        except ImportError:
            # Fallback for systems without torch_xla
            return self
