# ============================================================================
# ARKHE OS v∞.Ω.∇+++.12.3 — Synthetic Telemetry Generator
# Purpose: Generate realistic telemetry for bandit convergence testing
# ============================================================================

import numpy as np
from typing import Tuple
from bandit.kernel_variant import KernelVariant

class SyntheticTelemetryGenerator:
    """
    Generates synthetic telemetry with ground-truth optimal variant.

    The optimal variant has:
    - Lower latency than verified bound (15% margin)
    - Lower power than verified bound (10% margin)
    - Epsilon centered at 0.07 with low variance

    Non-optimal variants have random offsets and higher epsilon variance.
    """

    def __init__(
        self,
        optimal_variant_id: int,
        noise_scale_latency: float = 0.05,
        noise_scale_power: float = 0.05,
        noise_scale_epsilon: float = 0.01,
        seed: int = 42
    ):
        """
        Initialize telemetry generator.

        Args:
            optimal_variant_id: ID of the ground-truth optimal variant
            noise_scale_latency: Gaussian noise scale for latency (fraction of baseline)
            noise_scale_power: Gaussian noise scale for power
            noise_scale_epsilon: Standard deviation for epsilon sampling
            seed: Random seed for reproducibility
        """
        self.optimal_id = optimal_variant_id
        self.noise_lat = noise_scale_latency
        self.noise_pwr = noise_scale_power
        self.noise_eps = noise_scale_epsilon
        self.rng = np.random.default_rng(seed)

    def generate(
        self,
        variant: KernelVariant
    ) -> Tuple[float, float, float]:
        """
        Generate synthetic telemetry for a variant.

        Returns:
            (latency_us, power_mw, epsilon)
        """
        # Base values from verified bounds
        base_lat = variant.verified_latency_us
        base_pwr = variant.verified_power_mw

        # Determine if this is the optimal variant
        is_optimal = (variant.variant_id == self.optimal_id)

        if is_optimal:
            # Optimal variant: better than verified bounds
            lat_offset = -0.15  # 15% faster than worst-case
            pwr_offset = -0.10  # 10% more efficient
            eps_mean = 0.07     # Centered in mercy gap
            eps_std = 0.005     # Low variance (stable)
        else:
            # Non-optimal: random offsets within reasonable ranges
            lat_offset = self.rng.uniform(-0.05, 0.10)  # -5% to +10%
            pwr_offset = self.rng.uniform(-0.05, 0.10)
            eps_mean = self.rng.uniform(0.04, 0.10)     # Random center in gap
            eps_std = 0.01                               # Higher variance

        # Add Gaussian noise
        latency = base_lat * (1 + lat_offset) * (1 + self.rng.normal(0, self.noise_lat))
        power = base_pwr * (1 + pwr_offset) * (1 + self.rng.normal(0, self.noise_pwr))

        # Sample epsilon with clipping to realistic range
        epsilon = self.rng.normal(eps_mean, eps_std)
        epsilon = np.clip(epsilon, 0.02, 0.15)  # Allow some out-of-bounds for learning

        return float(latency), float(power), float(epsilon)

    def generate_batch(
        self,
        variant: KernelVariant,
        n_samples: int
    ) -> np.ndarray:
        """
        Generate batch of telemetry samples for statistical analysis.

        Returns:
            Array of shape (n_samples, 3) with columns [latency, power, epsilon]
        """
        samples = []
        for _ in range(n_samples):
            samples.append(self.generate(variant))
        return np.array(samples)