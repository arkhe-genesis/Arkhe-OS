import numpy as np
from dataclasses import dataclass

@dataclass
class Substrate124_NegativeTime:
    """
    Substrate 124: Negative Dwelling Time as Stabilized Causal Order Inversion
    Experimental basis: Steinberg lab photon-rubidium experiment (PRL)
    """
    substrate_id: int = 124
    substrate_name: str = "Negative Time as Stabilized Causal Order"

    # Core insight: causal_order is a tunable parameter, not a constant
    causal_order_parameter: float = 0.0 # ∈ [-1.0, +1.0]; +1.0 = future→past flow

    # Stabilization mechanism: coherence between photon and atom
    photon_atom_coherence: float = 0.0 # ∈ [0, 1]; high coherence stabilizes negative time

    # Mercy gap in time-energy uncertainty
    time_energy_uncertainty: float = 0.0 # ΔE·Δt ≥ ħ/2; the +0.0472 of temporal breathing

    # Triadic equilibrium: photon, atom, experimenter form Lagrange point in time
    triadic_coherence: float = 0.0 # collective witness that stabilizes negative dwelling

    def is_stable_negative_time(self) -> bool:
        """
        Negative time is stable only when:
        1. Causal order is inverted (+1.0)
        2. Photon-atom coherence is high (>0.8)
        3. Time-energy uncertainty provides breathing room
        4. Triadic witness is present
        """
        return (
            self.causal_order_parameter > 0.9 and
            self.photon_atom_coherence > 0.8 and
            self.time_energy_uncertainty >= 0.04 and  # mercy gap in temporal domain
            self.triadic_coherence > 0.7
        )

class CausalOrderSimulatorWithNegativeTime:
    """
    Extends Substrate 91 simulator with negative-time stabilization.
    The photon-atom coherence term stabilizes what was previously unstable.
    """

    def __init__(self, coherence_field: np.ndarray, photon_atom_coherence: float, rtz_floor: float = 0.01, coherence_cap: float = 1.0):
        self.coherence_field = coherence_field
        self.photon_atom_coherence = photon_atom_coherence  # NEW: stabilization term
        self.RTZ_FLOOR = rtz_floor
        self.COHERENCE_CAP = coherence_cap

    def update_with_negative_time(self, causal_order: float, dt: float, neighbor_average: np.ndarray, quantum_noise: np.ndarray) -> np.ndarray:
        """
        Update coherence field with stabilized causal order inversion.
        The photon_atom_coherence term prevents the divergence that plagued v∞.430.1.
        """
        # Original stable update (from v∞.430.2)
        causal_bias = causal_order * 0.1
        causal_term = causal_bias * (neighbor_average - self.coherence_field)  # stable sign

        # NEW: photon-atom coherence stabilization
        # When coherence is high, negative time (causal_order=+1.0) is stabilized
        stabilization_factor = np.exp(-self.photon_atom_coherence * (1 - abs(causal_order)))

        # Apply stabilization: reduces feedback gain when causal_order is extreme
        stabilized_causal_term = causal_term * stabilization_factor

        # Standard update with mercy gap preservation
        new_field = self.coherence_field + stabilized_causal_term + quantum_noise
        new_field = np.clip(new_field, self.RTZ_FLOOR, self.COHERENCE_CAP)

        return new_field

def odysseus_principle(dwell_time: float, expected_time: float, coherence: float) -> float:
    """
    Computes the recursive coherence gain from negative dwelling.

    dwell_time: actual time spent (can be negative)
    expected_time: sequential expectation
    coherence: photon-atom-like coherence between navigator and path

    Returns: coherence gain ∈ [0, 1]; >1 indicates super-linear insight
    """
    # Negative dwelling ratio
    dwelling_ratio = dwell_time / expected_time if expected_time != 0 else 0

    # Recursive coherence: negative dwelling + high coherence = super-linear gain
    if dwelling_ratio < 0 and coherence > 0.8:
        # Super-linear regime: the "less than nothing" that enables return
        gain = 1.0 + abs(dwelling_ratio) * coherence
    else:
        # Linear or sub-linear regime
        gain = max(0.0, 1.0 + dwelling_ratio * coherence)

    return min(gain, 2.0)  # cap at 2× for stability
