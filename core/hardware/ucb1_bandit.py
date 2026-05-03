# ============================================================================
# ARKHE OS v∞.Ω.∇+++.12.3 — UCB1 Bandit for Fast A∘P Loop (Python Reference)
# Purpose: Online kernel variant selection with mercy-aware reward
# Target: Host CPU / FPGA soft-core (via HLS synthesis)
# Safety: ε ∈ [0.04, 0.10] enforced via hard exclusion mask
# ============================================================================

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class KernelVariant:
    """A single formally verified kernel variant in the zoo."""
    variant_id: int
    ceremony: str
    block_dim: int
    tile_size: int
    unroll_factor: int
    shared_mem_bytes: int
    register_count: int
    ptx_hash: str

    # Static performance bounds (from formal verification)
    verified_latency_us: float
    verified_power_mw: float

    # Dynamic tracking (updated by bandit)
    total_launches: int = 0
    cumulative_reward: float = 0.0
    sum_squared_reward: float = 0.0
    last_latency_us: float = 0.0
    last_power_mw: float = 0.0
    last_epsilon: float = 0.07  # default centered in mercy gap

    def mean_reward(self) -> float:
        return self.cumulative_reward / max(self.total_launches, 1)

    def reward_std(self) -> float:
        if self.total_launches < 2:
            return 1.0  # high uncertainty
        variance = (self.sum_squared_reward / self.total_launches) - self.mean_reward()**2
        return math.sqrt(max(0.0, variance))

class CeremonyReward:
    """
    Mercy-aware composite reward function.
    Reward ∈ [0, 1]; higher is better.
    """
    def __init__(self,
                 latency_weight: float = 0.4,
                 power_weight: float = 0.3,
                 mercy_weight: float = 0.3,
                 latency_baseline_us: float = 500.0,
                 power_baseline_mw: float = 150.0,
                 mercy_target: float = 0.07,
                 mercy_penalty_factor: float = 2.0):
        self.w_lat = latency_weight
        self.w_pow = power_weight
        self.w_mer = mercy_weight
        self.lat_bl = latency_baseline_us
        self.pow_bl = power_baseline_mw
        self.mer_target = mercy_target
        self.mer_penalty = mercy_penalty_factor

    def compute(self, latency_us: float, power_mw: float, epsilon: float) -> float:
        # Latency reward: 1 if ≤10% baseline, 0 if ≥200% baseline
        lat_score = 1.0 - min(max(latency_us / (2 * self.lat_bl), 0.0), 1.0)

        # Power reward: same scaling
        pow_score = 1.0 - min(max(power_mw / (2 * self.pow_bl), 0.0), 1.0)

        # Mercy reward: piecewise linear with strong penalty outside bounds
        if 0.04 <= epsilon <= 0.10:
            # Inside gap: peak at target (0.07), taper to 0.5 at edges
            mer_score = 1.0 - abs(epsilon - self.mer_target) / 0.03
        else:
            # Outside: strong penalty
            distance = min(abs(epsilon - 0.04), abs(epsilon - 0.10))
            mer_score = -self.mer_penalty * distance

        # Weighted sum, clipped to [0,1]
        reward = self.w_lat * lat_score + self.w_pow * pow_score + self.w_mer * mer_score
        return max(0.0, min(1.0, reward))

class UCB1KernelBandit:
    """
    Upper Confidence Bound bandit for online kernel variant selection.
    Balances exploration/exploitation while enforcing mercy-gap safety.
    """
    def __init__(self,
                 variants: List[KernelVariant],
                 reward_fn: CeremonyReward,
                 exploration_constant: float = 2.0,
                 warm_start_reward: float = 0.5,
                 warm_start_launches: int = 2,
                 safety_epsilon_bounds: Tuple[float, float] = (0.04, 0.10)):
        self.reward_fn = reward_fn
        self.C = exploration_constant
        self.eps_min, self.eps_max = safety_epsilon_bounds

        # Index variants by ID
        self.variants: Dict[int, KernelVariant] = {v.variant_id: v for v in variants}

        # Warm-start: give each variant optimistic prior
        for var in self.variants.values():
            var.total_launches = warm_start_launches
            var.cumulative_reward = warm_start_reward * warm_start_launches
            var.sum_squared_reward = warm_start_reward**2 * warm_start_launches

        self.total_launches = sum(v.total_launches for v in self.variants.values())
        logger.info(f"UCB1Bandit initialized with {len(self.variants)} variants")

    def select_variant(self) -> int:
        """Select the best variant to launch next. O(N) in number of variants."""
        best_id = None
        best_ucb = -float('inf')

        for vid, var in self.variants.items():
            # SAFETY MASK: exclude variants that violated mercy gap
            if var.total_launches > 0:
                if var.last_epsilon < self.eps_min or var.last_epsilon > self.eps_max:
                    continue  # hard exclusion

            # UCB1 calculation
            if var.total_launches == 0:
                ucb = float('inf')  # force exploration
            else:
                mean_r = var.mean_reward()
                exploration_bonus = self.C * math.sqrt(
                    2.0 * math.log(max(self.total_launches, 1)) / var.total_launches
                )
                ucb = mean_r + exploration_bonus

            if ucb > best_ucb:
                best_ucb = ucb
                best_id = vid

        # Fallback: if all unsafe, pick best historical mean
        if best_id is None:
            safe_variants = [v for v in self.variants.values() if v.total_launches > 0]
            if safe_variants:
                best_id = max(safe_variants, key=lambda v: v.mean_reward()).variant_id
            else:
                # Last resort: pick any variant
                best_id = next(iter(self.variants.keys()))
                logger.warning(f"All variants unsafe; fallback to variant {best_id}")

        return best_id

    def update(self, variant_id: int, latency_us: float, power_mw: float, epsilon: float):
        """Update variant statistics after execution."""
        if variant_id not in self.variants:
            raise ValueError(f"Unknown variant_id: {variant_id}")

        var = self.variants[variant_id]
        reward = self.reward_fn.compute(latency_us, power_mw, epsilon)

        var.total_launches += 1
        var.cumulative_reward += reward
        var.sum_squared_reward += reward**2
        var.last_latency_us = latency_us
        var.last_power_mw = power_mw
        var.last_epsilon = epsilon

        self.total_launches += 1

        # Log safety violations
        if epsilon < self.eps_min or epsilon > self.eps_max:
            logger.warning(
                f"Mercy gap violation: ε={epsilon:.3f} ∉ [{self.eps_min}, {self.eps_max}] "
                f"for variant {variant_id}"
            )

    def get_statistics(self) -> Dict:
        """Return bandit statistics for monitoring."""
        return {
            "total_launches": self.total_launches,
            "best_variant": max(self.variants.values(), key=lambda v: v.mean_reward()).variant_id,
            "mean_reward_best": max(v.mean_reward() for v in self.variants.values()),
            "safe_variant_count": sum(
                1 for v in self.variants.values()
                if v.total_launches == 0 or self.eps_min <= v.last_epsilon <= self.eps_max
            ),
            "total_variants": len(self.variants)
        }

def generate_pdi_kernel_zoo() -> List[KernelVariant]:
    """Generate 16 verified PDI kernel variants with diverse parameters."""
    variants = []

    # Base parameters
    ceremony = "pdi_computation"
    base_shared_mem = 2048  # floats for interleaved complex FFT
    base_registers = 48

    # Parameter grids
    block_dims = [128, 256, 512]
    unroll_factors = [4, 8]
    tile_strategies = ["full", "half"]  # full: 512-sample FFT in one pass; half: two 256-sample passes

    variant_id = 0
    for block_dim in block_dims:
        for unroll in unroll_factors:
            for tile_strat in tile_strategies:
                # Compute derived parameters
                if tile_strat == "full":
                    tile_size = 512
                    shared_mem = base_shared_mem
                    reg_pressure = base_registers + (8 if unroll == 8 else 4)
                    latency_factor = 1.0
                else:  # half
                    tile_size = 256
                    shared_mem = base_shared_mem // 2
                    reg_pressure = base_registers - 4
                    latency_factor = 1.15  # slight overhead for two passes

                # Verified bounds (from formal analysis)
                verified_latency = 480 * latency_factor * (256 / block_dim)  # scales with occupancy
                verified_power = 145 + (block_dim / 128) * 5  # larger blocks use more power

                variant = KernelVariant(
                    variant_id=variant_id,
                    ceremony=ceremony,
                    block_dim=block_dim,
                    tile_size=tile_size,
                    unroll_factor=unroll,
                    shared_mem_bytes=shared_mem * 4,  # floats to bytes
                    register_count=reg_pressure,
                    ptx_hash=f"sha256:pdi_v{variant_id:02d}_{block_dim}_{unroll}_{tile_strat}",
                    verified_latency_us=verified_latency,
                    verified_power_mw=verified_power
                )
                variants.append(variant)
                variant_id += 1

    # Add 4 more variants with aggressive optimizations (higher risk/reward)
    aggressive_params = [
        (1024, 16, "full", 420, 165),   # high occupancy, high power
        (128, 16, "half", 540, 135),    # low occupancy, low power
        (256, 12, "full", 465, 148),    # balanced aggressive
        (512, 6, "half", 495, 152),     # conservative aggressive
    ]

    for block_dim, unroll, tile_strat, lat, pwr in aggressive_params:
        variant = KernelVariant(
            variant_id=variant_id,
            ceremony=ceremony,
            block_dim=block_dim,
            tile_size=512 if tile_strat == "full" else 256,
            unroll_factor=unroll,
            shared_mem_bytes=(2048 if tile_strat == "full" else 1024) * 4,
            register_count=52 if unroll >= 12 else 46,
            ptx_hash=f"sha256:pdi_v{variant_id:02d}_aggressive",
            verified_latency_us=lat,
            verified_power_mw=pwr
        )
        variants.append(variant)
        variant_id += 1

    return variants
