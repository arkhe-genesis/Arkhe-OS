# ============================================================================
# ARKHE OS v∞.Ω.∇+++.12.3 — UCB1KernelBandit: Online Kernel Variant Selection
# Purpose: Balance exploration/exploitation while enforcing mercy-gap safety
# Target: Host CPU for prototyping; can be synthesized to FPGA via HLS
# ============================================================================

from typing import Dict, List, Optional, Tuple
import math
import logging
import numpy as np

from .kernel_variant import KernelVariant
from .ceremony_reward import CeremonyReward

logger = logging.getLogger(__name__)

class UCB1KernelBandit:
    """
    Upper Confidence Bound (UCB1) bandit for online kernel variant selection.

    Key features:
    - Mercy-aware reward: epsilon preservation weighted equally with performance
    - Safety mask: hard exclusion of variants that violate mercy gap bounds
    - Warm-start: optimistic prior to encourage initial exploration
    - Fallback logic: graceful degradation if all variants become unsafe

    The bandit operates in the fast A∘P loop (µs-scale decision time).
    """

    def __init__(
        self,
        variants: List[KernelVariant],
        reward_fn: CeremonyReward,
        exploration_constant: float = 2.0,
        warm_start_reward: float = 0.5,
        warm_start_launches: int = 2,
        safety_epsilon_bounds: Tuple[float, float] = (0.04, 0.10),
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the bandit.

        Args:
            variants: List of formally verified kernel variants
            reward_fn: CeremonyReward instance for computing rewards
            exploration_constant: C in UCB1 formula; higher = more exploration
            warm_start_reward: Initial optimistic reward for untested variants
            warm_start_launches: Virtual launches to seed each variant
            safety_epsilon_bounds: (min, max) for mercy gap enforcement
            logger: Optional logger for bandit events
        """
        self.reward_fn = reward_fn
        self.C = exploration_constant
        self.eps_min, self.eps_max = safety_epsilon_bounds
        self.logger = logger or logging.getLogger(__name__)

        # Index variants by ID for O(1) lookup
        self.variants: Dict[int, KernelVariant] = {v.variant_id: v for v in variants}

        # Warm-start: give each variant optimistic prior to encourage exploration
        # Update via copy-on-write
        updated_variants = {}
        for vid, var in self.variants.items():
            updated_variants[vid] = var.copy_with_updates(
                total_launches=warm_start_launches,
                cumulative_reward=warm_start_reward * warm_start_launches,
                sum_squared_reward=warm_start_reward**2 * warm_start_launches
            )
        self.variants = updated_variants

        self.total_launches = sum(v.total_launches for v in self.variants.values())
        self.logger.info(
            f"UCB1Bandit initialized: {len(self.variants)} variants, "
            f"C={self.C}, ε∈[{self.eps_min}, {self.eps_max}]"
        )

    def select_variant(self) -> int:
        """
        Select the best variant to launch next.

        Returns:
            variant_id of selected kernel variant

        Complexity: O(N) in number of variants (typically 16-64, so < 10 µs on modern CPU)
        """
        best_id: Optional[int] = None
        best_ucb = -float('inf')

        for vid, var in self.variants.items():
            # ─── SAFETY MASK: HARD EXCLUSION ───
            # If variant has violated mercy gap, exclude it entirely
            if var.total_launches > 0:
                if var.last_epsilon < self.eps_min or var.last_epsilon > self.eps_max:
                    self.logger.debug(f"Variant {vid} excluded: ε={var.last_epsilon:.3f} out of bounds")
                    continue

            # ─── UCB1 CALCULATION ───
            if var.total_launches == 0:
                # Force exploration of never-launched variants
                ucb = float('inf')
            else:
                mean_reward = var.mean_reward()
                # UCB1 exploration bonus: C * sqrt(2 * ln(total) / n_i)
                exploration_bonus = self.C * math.sqrt(
                    2.0 * math.log(max(self.total_launches, 1)) / var.total_launches
                )
                ucb = mean_reward + exploration_bonus

            # Track best
            if ucb > best_ucb:
                best_ucb = ucb
                best_id = vid

        # ─── FALLBACK: ALL VARIANTS UNSAFE ───
        if best_id is None:
            self.logger.warning("All variants excluded by safety mask; falling back to best historical")
            # Pick variant with best mean reward among those with launches
            safe_variants = [v for v in self.variants.values() if v.total_launches > 0]
            if safe_variants:
                best_id = max(safe_variants, key=lambda v: v.mean_reward()).variant_id
            else:
                # Last resort: pick any variant (should not happen with warm-start)
                best_id = next(iter(self.variants.keys()))
                self.logger.error(f"Emergency fallback to variant {best_id}")

        return best_id

    def update(
        self,
        variant_id: int,
        latency_us: float,
        power_mw: float,
        epsilon: float
    ) -> float:
        """
        Update variant statistics after execution.

        Args:
            variant_id: ID of the variant that was executed
            latency_us: Measured latency in microseconds
            power_mw: Measured power in milliwatts
            epsilon: Measured mercy gap value

        Returns:
            Computed reward for this execution
        """
        if variant_id not in self.variants:
            raise ValueError(f"Unknown variant_id: {variant_id}")

        var = self.variants[variant_id]

        # Compute mercy-aware reward
        reward = self.reward_fn.compute(latency_us, power_mw, epsilon)

        # Update statistics via copy-on-write
        self.variants[variant_id] = var.copy_with_updates(
            total_launches=var.total_launches + 1,
            cumulative_reward=var.cumulative_reward + reward,
            sum_squared_reward=var.sum_squared_reward + reward**2,
            last_latency_us=latency_us,
            last_power_mw=power_mw,
            last_epsilon=epsilon
        )

        self.total_launches += 1

        # Log safety violations for monitoring
        if epsilon < self.eps_min or epsilon > self.eps_max:
            self.logger.warning(
                f"Mercy gap violation: ε={epsilon:.3f} ∉ [{self.eps_min}, {self.eps_max}] "
                f"for variant {variant_id} (reward={reward:.3f})"
            )

        return reward

    def get_statistics(self) -> Dict:
        """
        Return bandit statistics for monitoring and logging.

        Returns:
            dict with aggregate metrics
        """
        if not self.variants:
            return {}

        best_variant = max(self.variants.values(), key=lambda v: v.mean_reward())

        return {
            "total_launches": self.total_launches,
            "best_variant_id": best_variant.variant_id,
            "best_variant_mean_reward": best_variant.mean_reward(),
            "mean_reward_best": best_variant.mean_reward(),
            "safe_variant_count": sum(
                1 for v in self.variants.values()
                if v.total_launches == 0 or v.is_safe(self.eps_min, self.eps_max)
            ),
            "total_variants": len(self.variants),
            "avg_epsilon": np.mean([v.last_epsilon for v in self.variants.values() if v.total_launches > 0])
        }

    def get_variant(self, variant_id: int) -> Optional[KernelVariant]:
        """Get variant by ID."""
        return self.variants.get(variant_id)

    def list_variants(self) -> List[KernelVariant]:
        """List all variants."""
        return list(self.variants.values())