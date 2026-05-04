# ============================================================================
# ARKHE OS v∞.Ω.∇+++.12.3 — CeremonyReward: Mercy-Aware Composite Reward
# Purpose: Compute scalar reward from latency, power, and mercy gap (epsilon)
# ============================================================================

from dataclasses import dataclass
from typing import Tuple

@dataclass
class CeremonyReward:
    """
    Computes reward ∈ [0, 1] from execution telemetry.

    The reward is a weighted composite of:
    - Latency: lower is better (minimization objective)
    - Power: lower is better (minimization objective)
    - Mercy gap (epsilon): optimal at target (0.07), penalized outside [0.04, 0.10]

    Weights reflect ceremony priorities:
    - Real-time tDCS: latency_weight=0.6, power_weight=0.2, mercy_weight=0.2
    - Background ZK: latency_weight=0.2, power_weight=0.6, mercy_weight=0.2
    - Orthogonal witness (default): balanced weights
    """

    # Weight configuration
    latency_weight: float = 0.4
    power_weight: float = 0.3
    mercy_weight: float = 0.3

    # Baseline values for normalization
    latency_baseline_us: float = 500.0
    power_baseline_mw: float = 150.0

    # Mercy gap configuration
    mercy_target: float = 0.07  # Ideal epsilon value
    mercy_penalty_factor: float = 2.0  # Penalty multiplier for out-of-bounds epsilon

    # Valid bounds for mercy gap
    mercy_min: float = 0.04
    mercy_max: float = 0.10

    def compute(self, latency_us: float, power_mw: float, epsilon: float) -> float:
        """
        Compute composite reward from telemetry.

        Args:
            latency_us: Measured kernel latency in microseconds
            power_mw: Measured power consumption in milliwatts
            epsilon: Measured mercy gap value (should be in [0.04, 0.10])

        Returns:
            Reward in [0, 1]; higher is better
        """
        # ─── LATENCY REWARD ───
        # Score = 1.0 if latency <= 10% of baseline
        # Score = 0.0 if latency >= 200% of baseline
        # Linear interpolation between
        lat_ratio = latency_us / (2 * self.latency_baseline_us)
        lat_score = 1.0 - min(max(lat_ratio, 0.0), 1.0)

        # ─── POWER REWARD ───
        # Same scaling as latency
        pow_ratio = power_mw / (2 * self.power_baseline_mw)
        pow_score = 1.0 - min(max(pow_ratio, 0.0), 1.0)

        # ─── MERCY GAP REWARD ───
        # Piecewise linear with strong penalty outside bounds
        if self.mercy_min <= epsilon <= self.mercy_max:
            # Inside gap: peak at target (0.07), taper linearly to 0.5 at edges
            distance_from_target = abs(epsilon - self.mercy_target)
            mer_score = 1.0 - distance_from_target / 0.03  # 0.03 = half-gap width
        else:
            # Outside gap: strong penalty, score can go negative
            distance_to_nearest_bound = min(
                abs(epsilon - self.mercy_min),
                abs(epsilon - self.mercy_max)
            )
            mer_score = -self.mercy_penalty_factor * distance_to_nearest_bound

        # ─── WEIGHTED COMPOSITE ───
        reward = (
            self.latency_weight * lat_score +
            self.power_weight * pow_score +
            self.mercy_weight * mer_score
        )

        # Clip to [0, 1] for reward accumulation (prevents negative rewards from destabilizing UCB)
        return max(0.0, min(1.0, reward))

    def compute_with_components(self, latency_us: float, power_mw: float, epsilon: float) -> dict:
        """
        Compute reward and return individual component scores for debugging.

        Returns:
            dict with 'reward', 'lat_score', 'pow_score', 'mer_score'
        """
        lat_ratio = latency_us / (2 * self.latency_baseline_us)
        lat_score = 1.0 - min(max(lat_ratio, 0.0), 1.0)

        pow_ratio = power_mw / (2 * self.power_baseline_mw)
        pow_score = 1.0 - min(max(pow_ratio, 0.0), 1.0)

        if self.mercy_min <= epsilon <= self.mercy_max:
            distance_from_target = abs(epsilon - self.mercy_target)
            mer_score = 1.0 - distance_from_target / 0.03
        else:
            distance_to_nearest_bound = min(
                abs(epsilon - self.mercy_min),
                abs(epsilon - self.mercy_max)
            )
            mer_score = -self.mercy_penalty_factor * distance_to_nearest_bound

        reward = (
            self.latency_weight * lat_score +
            self.power_weight * pow_score +
            self.mercy_weight * mer_score
        )
        reward = max(0.0, min(1.0, reward))

        return {
            'reward': reward,
            'lat_score': lat_score,
            'pow_score': pow_score,
            'mer_score': mer_score,
            'epsilon_in_gap': self.mercy_min <= epsilon <= self.mercy_max
        }