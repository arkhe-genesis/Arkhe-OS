from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

@dataclass
class KernelVariant:
    """A single verified kernel variant in the zoo."""
    variant_id: int
    ceremony: str                # e.g., "pdi_computation"
    block_dim: int               # e.g., 128, 256, 512
    tile_size: int               # for STARK NTT, etc.
    unroll_factor: int
    shared_mem_bytes: int
    register_count: int          # per-thread register pressure
    ptx_hash: str                # SHA-256 of the PTX code (or SASS hash)

    # Static performance bounds (from formal verification)
    verified_latency_us: float   # worst-case bound
    verified_power_mw: float     # theoretical minimum

    # Dynamic tracking (updated by bandit)
    total_launches: int = 0
    cumulative_reward: float = 0.0
    sum_squared_reward: float = 0.0
    last_latency_us: float = 0.0
    last_power_mw: float = 0.0
    last_epsilon: float = 0.07   # default mercy gap

class KernelZoo:
    """Registry of all verified kernel variants for a single ceremony."""
    def __init__(self, ceremony: str):
        self.ceremony = ceremony
        self.variants: Dict[int, KernelVariant] = {}

    def add_variant(self, variant: KernelVariant):
        self.variants[variant.variant_id] = variant

    def get_variant(self, variant_id: int) -> KernelVariant:
        return self.variants[variant_id]

    def all_ids(self) -> List[int]:
        return list(self.variants.keys())

    def num_variants(self) -> int:
        return len(self.variants)

class CeremonyReward:
    """
    Computes reward from execution telemetry for a single kernel launch.
    The reward is in [0, 1]; higher is better.
    """
    def __init__(self,
                 latency_weight: float = 0.4,
                 power_weight: float = 0.3,
                 mercy_weight: float = 0.3,
                 latency_baseline_us: float = 500.0,   # expected latency
                 power_baseline_mw: float = 150.0,     # expected power
                 mercy_target: float = 0.07,           # ideal epsilon
                 mercy_penalty_factor: float = 2.0):   # penalty multiplier for out-of-bounds
        self.w_lat = latency_weight
        self.w_pow = power_weight
        self.w_mer = mercy_weight
        self.lat_bl = latency_baseline_us
        self.pow_bl = power_baseline_mw
        self.mer_target = mercy_target
        self.mer_penalty = mercy_penalty_factor

    def compute(self, latency_us: float, power_mw: float, epsilon: float) -> float:
        """
        Compute reward in [0,1].
        Latency and power are minimisation objectives; they contribute more when below baseline.
        Mercy gap is maximised when epsilon in [0.04, 0.10], heavily penalised outside.
        """
        lat_score = 1.0 - min(max(latency_us / (2 * self.lat_bl), 0.0), 1.0)
        pow_score = 1.0 - min(max(power_mw / (2 * self.pow_bl), 0.0), 1.0)

        if 0.04 <= epsilon <= 0.10:
            mer_score = 1.0 - abs(epsilon - self.mer_target) / 0.03
        else:
            distance = min(abs(epsilon - 0.04), abs(epsilon - 0.10))
            mer_score = -self.mer_penalty * distance

        reward = self.w_lat * lat_score + self.w_pow * pow_score + self.w_mer * mer_score
        return max(0.0, min(1.0, reward))

class UCB1KernelBandit:
    """
    Upper Confidence Bound bandit for online kernel variant selection.
    Balances exploitation of fast/low-power variants with exploration
    of under-tested ones, while respecting the mercy-gap safety constraint.
    """
    def __init__(self,
                 zoo: KernelZoo,
                 reward_fn: CeremonyReward,
                 exploration_constant: float = 2.0,
                 warm_start_reward: float = 0.5,
                 safety_epsilon_bounds: Tuple[float, float] = (0.04, 0.10)):
        self.zoo = zoo
        self.reward_fn = reward_fn
        self.C = exploration_constant
        self.warm_start_reward = warm_start_reward
        self.eps_min, self.eps_max = safety_epsilon_bounds

        # Warm-start all variants with a small number of virtual launches
        for vid, var in self.zoo.variants.items():
            var.total_launches = 2           # virtual launches for prior
            var.cumulative_reward = warm_start_reward * 2
            var.sum_squared_reward = warm_start_reward**2 * 2

    def select_variant(self, total_launches: int) -> int:
        """Select the best variant to launch next."""
        best_id = None
        best_ucb = -float('inf')

        for vid in self.zoo.all_ids():
            var = self.zoo.get_variant(vid)

            # Safety: if last epsilon was outside bounds, exclude this variant
            if var.total_launches > 0:
                if var.last_epsilon < self.eps_min or var.last_epsilon > self.eps_max:
                    continue  # skip unsafe variant

            # UCB calculation
            if var.total_launches == 0:
                ucb = float('inf')   # force exploration if never launched
            else:
                mean_reward = var.cumulative_reward / var.total_launches
                exploration_bonus = self.C * math.sqrt(2.0 * math.log(total_launches) / var.total_launches)
                ucb = mean_reward + exploration_bonus

            if ucb > best_ucb:
                best_ucb = ucb
                best_id = vid

        # Fallback: if all variants are unsafe, pick the one with best mean reward
        if best_id is None:
            best_id = max(self.zoo.all_ids(), key=lambda vid:
                self.zoo.get_variant(vid).cumulative_reward / max(self.zoo.get_variant(vid).total_launches, 1))

        return best_id

    def update(self, variant_id: int, latency_us: float, power_mw: float, epsilon: float):
        """Update the variant's statistics after execution."""
        var = self.zoo.get_variant(variant_id)
        reward = self.reward_fn.compute(latency_us, power_mw, epsilon)

        var.total_launches += 1
        var.cumulative_reward += reward
        var.sum_squared_reward += reward**2
        var.last_latency_us = latency_us
        var.last_power_mw = power_mw
        var.last_epsilon = epsilon

    def best_arm_mean(self) -> float:
        """Return the mean reward of the currently best variant."""
        best_id = max(self.zoo.all_ids(), key=lambda vid:
            self.zoo.get_variant(vid).cumulative_reward / max(self.zoo.get_variant(vid).total_launches, 1))
        var = self.zoo.get_variant(best_id)
        return var.cumulative_reward / max(var.total_launches, 1)
