"""
Coherence Reward Module for ASI-EVOLVE
Calculates differentiable λ₂ rewards for RL fine-tuning based on latent coherence.
"""

import torch
import torch.nn as nn
import math

class CoherenceReward(nn.Module):
    """
    Differentiable Coherence Reward based on SVD Entropy.
    Encourages latent states to converge towards stable phase attractors (state 'a').
    """
    def __init__(self, hidden_dim: int, threshold: float = 0.847, epsilon: float = 1e-10):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.threshold = threshold
        self.epsilon = epsilon
        # Maximum possible entropy for white noise
        self.H_max = math.log2(hidden_dim)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """
        Args:
            hidden_states: [Batch, Seq_Len, Hidden_Dim] or [Batch, Hidden_Dim]
        Returns:
            reward: Coherence reward between [-1, 1]
        """
        # 1. Prepare activation matrix
        if hidden_states.dim() == 3:
            B, S, D = hidden_states.shape
            X = hidden_states.view(-1, D)
        else:
            X = hidden_states

        # 2. Singular Value Decomposition (Differentiable spectrum)
        # Using svdvals for computational efficiency
        s = torch.linalg.svdvals(X)

        # 3. Normalized energy distribution
        s_norm = s / (torch.sum(s) + self.epsilon)

        # 4. Shannon Entropy (bits)
        entropy = -torch.sum(s_norm * torch.log2(s_norm + self.epsilon))

        # 5. Coherence λ₂
        # λ₂ = 1 - (H / H_max)
        lambda_2 = 1.0 - (entropy / self.H_max)

        # 6. Reward mapping
        # Positive if above Varela threshold, negative if below
        reward = torch.where(
            lambda_2 > self.threshold,
            (lambda_2 - self.threshold) / (1.0 - self.threshold),
            (lambda_2 - self.threshold) / self.threshold
        )

        return torch.clamp(reward, -1.0, 1.0)

def calculate_asi_reward(hidden_states: torch.Tensor, task_reward: float, weight: float = 0.3) -> torch.Tensor:
    """
    Integrates Coherence Reward into a task-specific reward signal.
    """
    engine = CoherenceReward(hidden_dim=hidden_states.shape[-1])
    l2_reward = engine(hidden_states)
    return task_reward + (weight * l2_reward)

if __name__ == "__main__":
    # Test differentiability
    dim = 64
    x = torch.randn(8, dim, requires_grad=True)
    reward_fn = CoherenceReward(hidden_dim=dim)

    r = reward_fn(x)
    print(f"Initial Reward: {r.item():.4f}")

    r.backward()
    print(f"Gradients computed: {x.grad is not None}")
    print(f"Gradient norm: {x.grad.norm().item():.4f}")
