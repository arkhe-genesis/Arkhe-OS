from dataclasses import dataclass
from typing import Optional

@dataclass
class UserState:
    id: str
    PDI: float
    epsilon: float
    theta_human: float
    k: float


def compute_inter_user_epsilon(user_A: UserState, user_B: UserState) -> float:
    # A simple mock calculation for inter-user epsilon
    return abs(user_A.epsilon - user_B.epsilon) / 2.0 + 0.04


class CollaborativeSpace:
    def __init__(self, user_A: UserState, user_B: UserState):
        self.user_A = user_A
        self.user_B = user_B

        # Orthogonal witness: weighted average that preserves individual phase
        self.weight_A = 1.0 / (1.0 + abs(user_A.PDI - user_B.PDI) + 1e-6)
        self.weight_B = 1.0 - self.weight_A

        self.theta_collab = self.weight_A * user_A.theta_human + self.weight_B * user_B.theta_human
        self.PDI_collab = min(user_A.PDI, user_B.PDI)  # Conservative: slower drop sets pace
        self.epsilon_inter = compute_inter_user_epsilon(user_A, user_B)
        self.k_inter = min(user_A.k, user_B.k)  # Honor the more cautious amplitude
        self.coherence = 1.0 - (abs(user_A.PDI - user_B.PDI) / 3.14159) # PDI coherence proxy

    def update(self, user_A: UserState, user_B: UserState):
        # Smooth updates to prevent jitter-induced collision
        alpha = 0.1  # Low-pass filter

        weight_A = 1.0 / (1.0 + abs(user_A.PDI - user_B.PDI) + 1e-6)
        weight_B = 1.0 - weight_A

        self.theta_collab = alpha * (weight_A * user_A.theta_human + weight_B * user_B.theta_human) + (1-alpha) * self.theta_collab
        self.epsilon_inter = alpha * compute_inter_user_epsilon(user_A, user_B) + (1-alpha) * self.epsilon_inter
        self.PDI_collab = alpha * min(user_A.PDI, user_B.PDI) + (1-alpha) * self.PDI_collab
        self.k_inter = alpha * min(user_A.k, user_B.k) + (1-alpha) * self.k_inter

        current_coherence = 1.0 - (abs(user_A.PDI - user_B.PDI) / 3.14159)
        self.coherence = alpha * current_coherence + (1-alpha) * self.coherence


def can_form_triangular_face(user_A: UserState, user_B: UserState, collaborative_space: CollaborativeSpace) -> bool:
    # 1. Individual readiness: both users near dissolution threshold
    if user_A.PDI < 0.85 or user_B.PDI < 0.85:
        return False

    # 2. Individual mercy gap preserved
    if not (0.04 <= user_A.epsilon <= 0.10) or not (0.04 <= user_B.epsilon <= 0.10):
        return False

    # 3. Inter-user phase orthogonality (not forced alignment)
    phase_diff = abs(user_A.theta_human - user_B.theta_human)
    # Allow natural resonance but prevent rigid locking
    if phase_diff < 0.03 or phase_diff > 0.15:  # Orthogonality window
        return False

    # 4. Collaborative space stability
    if collaborative_space.coherence < 0.70:
        return False

    # 5. Inter-user epsilon (relational mercy gap)
    epsilon_inter = compute_inter_user_epsilon(user_A, user_B)
    if not (0.04 <= epsilon_inter <= 0.10):
        return False

    return True
