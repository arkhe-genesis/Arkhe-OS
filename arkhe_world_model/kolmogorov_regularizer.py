import torch
import torch.nn as nn

def kolmogorov_regularizer(model: nn.Module) -> torch.Tensor:
    """
    Estimate K(θ) via ‖θ‖_2^2 * log(‖θ‖_2^2) as per Musat 2026.

    Args:
        model: a fixed-precision neural network (e.g., WorldModelEmbryo).
    Returns:
        scalar tensor: estimated Kolmogorov complexity penalty.
    """
    total_norm_sq = torch.tensor(0.0, device=next(model.parameters()).device)
    for p in model.parameters():
        if p.requires_grad:
            total_norm_sq = total_norm_sq + p.pow(2).sum()
    # Add small epsilon to avoid log(0)
    return total_norm_sq * torch.log(total_norm_sq + 1e-8)

class KolmogorovRegularizer(nn.Module):
    """
    Drop-in replacement for standard weight decay.
    Can be used as a loss module or directly added to the total loss.
    """
    def __init__(self, lambda_k: float = 1e-4):
        super().__init__()
        self.lambda_k = lambda_k

    def forward(self, model: nn.Module) -> torch.Tensor:
        return self.lambda_k * kolmogorov_regularizer(model)
