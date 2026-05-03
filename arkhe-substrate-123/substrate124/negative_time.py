# ============================================================================
# ARKHE OS v∞.Ω.∇+++.12.3 — Substrate 124: Negative Time as Stabilized Causal Order
# Experimental basis: Steinberg lab photon-rubidium experiment (PRL)
# ============================================================================

from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class Substrate124_NegativeTime:
    """
    Substrate 124: Negative Dwelling Time as Stabilized Causal Order Inversion.

    Core insight: causal_order is a tunable parameter, not a constant.
    When photon-atom coherence is high, causal_order = +1.0 (future→past)
    becomes stable rather than divergent.

    Experimental signature: photon exits cloud before average entry time,
    with atoms corroborating negative dwelling interval.
    """

    substrate_id: int = 124
    substrate_name: str = "Negative Time as Stabilized Causal Order"

    # Core parameter: causal order inversion
    # -1.0 = past→future (standard), 0.0 = atemporal, +1.0 = future→past
    causal_order_parameter: float  # ∈ [-1.0, +1.0]

    # Stabilization mechanism: photon-atom coherence
    # High coherence (>0.8) stabilizes negative-time dynamics
    photon_atom_coherence: float  # ∈ [0, 1]

    # Mercy gap in time-energy uncertainty domain
    # ΔE·Δt ≥ ħ/2 provides breathing room for temporal phase
    time_energy_uncertainty: float  # ∈ [0, ∞); ≥0.04 for stability

    # Triadic equilibrium: photon + atom + experimenter form Lagrange point in time
    triadic_coherence: float  # ∈ [0, 1]; collective witness stabilizes negative dwelling

    def is_stable_negative_time(self) -> bool:
        """
        Check if negative time configuration is stable.

        Negative time is stable only when:
        1. Causal order is inverted (causal_order > 0.9)
        2. Photon-atom coherence is high (>0.8)
        3. Time-energy uncertainty provides breathing room (≥0.04)
        4. Triadic witness is present (>0.7)

        Returns:
            True if configuration is stable for negative-time operation
        """
        return (
            self.causal_order_parameter > 0.9 and
            self.photon_atom_coherence > 0.8 and
            self.time_energy_uncertainty >= 0.04 and
            self.triadic_coherence > 0.7
        )

    def compute_effective_causal_bias(self) -> float:
        """
        Compute effective causal bias with coherence stabilization.

        The photon_atom_coherence term reduces feedback gain when
        causal_order is extreme, preventing the divergence that plagued
        the original Substrate 91 implementation.

        Returns:
            Stabilized causal bias ∈ [-0.1, +0.1]
        """
        base_bias = self.causal_order_parameter * 0.1

        # Stabilization factor: exponential decay with (1 - |causal_order|)
        # When coherence is high and |causal_order| is high, factor ≈ 1
        # When coherence is low or |causal_order| is low, factor < 1
        stabilization_factor = np.exp(
            -self.photon_atom_coherence * (1 - abs(self.causal_order_parameter))
        )

        return base_bias * stabilization_factor

    def to_dict(self) -> dict:
        """Serialize to dictionary for logging/serialization."""
        return {
            "substrate_id": self.substrate_id,
            "substrate_name": self.substrate_name,
            "causal_order_parameter": self.causal_order_parameter,
            "photon_atom_coherence": self.photon_atom_coherence,
            "time_energy_uncertainty": self.time_energy_uncertainty,
            "triadic_coherence": self.triadic_coherence,
            "is_stable": self.is_stable_negative_time(),
            "effective_causal_bias": self.compute_effective_causal_bias()
        }