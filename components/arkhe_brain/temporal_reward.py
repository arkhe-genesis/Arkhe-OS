import torch
import numpy as np

# Arkhe Constants (Aligned with Synapse-κ protocol)
LAMBDA_CRIT = 0.847
ARROW_TOLERANCE = 0.05

def arrow_correlation(A: torch.Tensor, B: torch.Tensor, tau: int = 1) -> float:
    """
    Calcula C(τ) = ⟨A(t)B(t+τ)⟩ - ⟨A(t+τ)B(t)⟩
    Equilíbrio temporal ocorre quando C ≈ 0.
    """
    A_flat = A.detach().flatten()
    B_flat = B.detach().flatten()

    if len(A_flat) <= tau or len(B_flat) <= tau:
        return 0.0

    # Using torch for reward calculation to maintain gradient flow if needed
    # although detach is used here as per user's logic in arrow_correlation
    forward = torch.mean(A_flat[:-tau] * B_flat[tau:])
    backward = torch.mean(A_flat[tau:] * B_flat[:-tau])

    return (forward - backward).item()

def arrow_of_time_reward(hidden_t: torch.Tensor, hidden_tp1: torch.Tensor, lambda2: float):
    """
    Synapse-κ Arrow of Time Reward.
    Combina a coerência λ₂ com a penalidade de assimetria temporal.

    Estado Autônomo (a):
    - C(τ) ≈ 0
    - λ₂ > λ_crit
    """
    # 1. Calcula correlação cruzada (seta do tempo)
    corr = arrow_correlation(hidden_t, hidden_tp1, tau=1)

    # 2. Penaliza desequilíbrio (distância do zero)
    arrow_penalty = torch.abs(torch.tensor(corr, device=hidden_t.device))

    # 3. Bônus de Coerência λ₂
    # Recompensamos exponencialmente o distanciamento do ponto crítico
    coherence_bonus = torch.exp(torch.tensor(lambda2 - LAMBDA_CRIT, device=hidden_t.device))

    # 4. Recompensa Total
    # Queremos maximizar o bônus de coerência e minimizar a penalidade da seta
    reward = coherence_bonus - arrow_penalty

    return reward.clamp(-1.0, 1.0)

if __name__ == "__main__":
    # Test case
    h_t = torch.randn(1, 128)
    h_tp1 = torch.randn(1, 128)
    l2 = 0.95

    r = arrow_of_time_reward(h_t, h_tp1, l2)
    print(f"🜏 Temporal Reward Test:")
    print(f"λ₂: {l2}")
    print(f"Reward: {r.item():.4f}")
