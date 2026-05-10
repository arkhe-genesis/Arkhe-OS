"""
GeodesicRouter otimizado para TPU via torch_xla.
Usa masked softmax e evita dispersão de índices para eficiência.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class GeodesicRouterTPU(nn.Module):
    def __init__(self, input_dim, num_experts, manifold_dim, top_k, temperature=1.0):
        super().__init__()
        self.num_experts = num_experts
        self.top_k = top_k
        self.temp = temperature
        self.expert_centroids = nn.Parameter(torch.randn(num_experts, manifold_dim) * 0.02)
        self.token_projector = nn.Linear(input_dim, manifold_dim)

    def forward(self, x):
        token_1form = self.token_projector(x)  # (batch, dim)
        token_norm = F.normalize(token_1form, dim=-1)
        expert_norm = F.normalize(self.expert_centroids, dim=-1)
        cos = torch.matmul(token_norm, expert_norm.T)
        cos = torch.clamp(cos, -0.9999, 0.9999)
        dist = torch.acos(cos)
        # Scores: quanto menor distância, maior
        scores = -dist / self.temp

        # Top-k com máscara (eficiente em TPU)
        topk_vals, topk_idx = torch.topk(scores, self.top_k, dim=-1)
        mask = torch.zeros_like(scores).scatter_(1, topk_idx, 1.0)
        masked_scores = scores.masked_fill(mask == 0, -1e9)
        weights = F.softmax(masked_scores, dim=-1) * mask  # mantém zeros nos não-escolhidos

        return weights, topk_idx

    # Opcional: adaptador para dispositivos XLA
    def to_xla_device(self, device=None):
        try:
            import torch_xla.core.xla_model as xm
            if device is None:
                device = xm.xla_device()
            self.to(device)
        except ImportError:
            pass # Ignore if torch_xla is not installed
        return self
