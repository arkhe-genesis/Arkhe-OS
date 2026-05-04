# ============================================================================
# ARKHE OS v∞.Ω.∇+++.12.3 — KernelVariant Dataclass
# Purpose: Immutable representation of a formally verified kernel variant
# ============================================================================

from dataclasses import dataclass, field
from typing import Optional
import hashlib

@dataclass(frozen=True)
class KernelVariant:
    """
    A single formally verified kernel variant in the zoo.

    All fields are immutable (frozen) to ensure reproducibility.
    Dynamic tracking fields are updated via copy-on-write by the bandit.
    """
    # Identity & specification
    variant_id: int
    ceremony: str  # e.g., "pdi_computation", "stark_ntt"
    block_dim: int  # CUDA block dimension (threads per block)
    tile_size: int  # For tile-based kernels (e.g., NTT)
    unroll_factor: int  # Loop unrolling factor
    shared_mem_bytes: int  # Shared memory requirement in bytes
    register_count: int  # Registers per thread
    ptx_hash: str  # SHA-256 of PTX source (or SASS hash)

    # Static performance bounds (from formal verification)
    verified_latency_us: float  # Worst-case latency bound
    verified_power_mw: float  # Theoretical minimum power

    # Dynamic tracking (updated by bandit via copy-on-write)
    total_launches: int = field(default=0, compare=False)
    cumulative_reward: float = field(default=0.0, compare=False)
    sum_squared_reward: float = field(default=0.0, compare=False)
    last_latency_us: float = field(default=0.0, compare=False)
    last_power_mw: float = field(default=0.0, compare=False)
    last_epsilon: float = field(default=0.07, compare=False)  # Centered in mercy gap

    def copy_with_updates(self, **kwargs) -> 'KernelVariant':
        """Create a new variant with updated dynamic fields (copy-on-write)."""
        return KernelVariant(**{**self.__dict__, **kwargs})

    def mean_reward(self) -> float:
        """Compute mean reward from cumulative statistics."""
        return self.cumulative_reward / max(self.total_launches, 1)

    def reward_std(self) -> float:
        """Compute standard deviation of reward (for uncertainty estimation)."""
        if self.total_launches < 2:
            return 1.0  # High uncertainty with few samples
        mean = self.mean_reward()
        variance = (self.sum_squared_reward / self.total_launches) - mean**2
        return (max(0.0, variance))**0.5

    def is_safe(self, eps_min: float = 0.04, eps_max: float = 0.10) -> bool:
        """Check if last epsilon was within mercy gap bounds."""
        if self.total_launches == 0:
            return True  # Untested variants are assumed safe until proven otherwise
        return eps_min <= self.last_epsilon <= eps_max

    def __hash__(self):
        return hash(self.variant_id)