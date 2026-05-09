"""
Archimedes-Ω Combined Protocol Optimizer
==========================================
Calculates optimal interval between LIPUS therapy and quantum drug delivery
to maximize BBE permeability and clearance efficiency.

Author: Arkhe Consortium
Version: 2.2.0 (Multimodal Synchronization)
"""

import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TissueState(Enum):
    """States of BBE permeability after LIPUS intervention."""
    BASAL = 0          # Normal resting state
    PRIMED = 1         # Increased permeability (0-2h post-LIPUS)
    PEAK_OPEN = 2      # Maximum permeability (2-4h post-LIPUS)
    CLOSING = 3       # Permeability decreasing (4-6h post-LIPUS)
    SEALED = 4       # Return to basal (6h+ post-LIPUS)

@dataclass
class LIPUSParameters:
    """Input parameters for LIPUS session."""
    intensity_mw_cm2: float        # Spatial-average temporal-mean intensity (mW/cm²)
    frequency_mhz: float          # Frequency (MHz) - typically 1.0-1.5 for brain
    duration_minutes: float       # Treatment duration (minutes)
    mi: float                     # Mechanical Index (must stay < 0.6 for safety)

    def validate(self) -> bool:
        """Ensures LIPUS parameters are within safe clinical limits."""
        if self.mi >= 0.6:
            raise ValueError("Mechanical Index exceeds safety threshold (0.6)")
        if self.intensity_mw_cm2 > 300:
            raise ValueError("Intensity exceeds safe limit (300 mW/cm²)")
        if self.frequency_mhz < 0.5 or self.frequency_mhz > 3.0:
            raise ValueError("Frequency outside therapeutic range (0.5-3.0 MHz)")
        return True

@dataclass
class DrugPayload:
    """Quantum-enhanced drug characteristics."""
    particle_size_nm: float         # Nanoparticle diameter
    surface_charge_mv: float      # Zeta potential (mV)
    entanglement_degree: float       # 0-1 coherence factor
    half_life_hours: float         # Circulation half-life

@dataclass
class CombinedProtocolResult:
    """Output of the optimization algorithm."""
    optimal_interval_hours: float
    predicted_absorption_efficiency: float
    clearance_boost_factor: float
    safety_margin: float
    tissue_states: List[Tuple[float, str]]
    recommendation: str

class CombinedProtocolOptimizer:
    """
    Optimizes timing between LIPUS and quantum drug delivery.

    The model uses a phase-coupled oscillator where:
    - LIPUS creates a "priming" window (2-4 hours post-exposure)
    - Drug absorption follows a Gaussian profile centered at t_peak
    - Entanglement degree modulates the effective permeability
    """

    # Time constants (hours) for tissue state transitions
    TAU_PRIME_OPEN = 2.0   # Time to reach peak permeability
    TAU_PRIME_CLOSE = 4.0   # Time to close after peak
    TAU_SEALED = 6.0       # Time to return to basal

    def __init__(self, lipus: LIPUSParameters, drug: DrugPayload):
        self.lipus = lipus
        self.drug = drug
        self._validate_inputs()

    def _validate_inputs(self):
        self.lipus.validate()
        if self.drug.particle_size_nm > 200:
            raise ValueError("Particle size too large for BBE crossing")

    def _permeability_model(self, t_hours: float) -> float:
        """
        Models BBE permeability as a function of time post-LIPUS.
        Uses a damped oscillation to simulate tissue "memory" of the mechanical pulse.
        """
        # Base permeability increase scaled by LIPUS intensity
        base_permeability = 1.0 + (self.lipus.intensity_mw_cm2 / 100.0)

        # Damped oscillation representing mechanobiologic response
        omega = 2 * np.pi / self.TAU_PRIME_OPEN  # Characteristic frequency
        damping = 0.15  # Decay rate

        # Gaussian envelope centered at t=2h (peak opening)
        envelope = np.exp(-((t_hours - 2.0) ** 2) / (2 * 1.5 ** 2))

        # Oscillatory component (tissue resonance)
        oscillation = np.exp(-damping * t_hours) * np.cos(omega * t_hours)

        # Entanglement degree modulates coherence transfer
        coherence_factor = 1.0 + (self.drug.entanglement_degree * 0.5)

        return base_permeability * envelope * coherence_factor * (1.0 + 0.2 * oscillation)

    def _absorption_efficiency(self, t_hours: float) -> float:
        """
        Calculates drug absorption efficiency at time t.
        Accounts for particle size and surface charge effects.
        """
        perm = self._permeability_model(t_hours)

        # Size penalty: smaller particles cross more easily
        size_factor = max(0, 1.0 - (self.drug.particle_size_nm / 200.0))

        # Charge attraction: negative charge on BBE attracts positive particles
        charge_factor = 1.0 + (np.tanh(self.drug.surface_charge_mv / 30.0) * 0.3)

        return perm * size_factor * charge_factor

    def _clearance_boost(self, t_hours: float) -> float:
        """
        Models the clearance boost from combined LIPUS + drug.
        Synergistic effect: LIPUS clears Aβ, drug enhances microglial activation.
        """
        perm = self._permeability_model(t_hours)

        # Synergy: entanglement degree amplifies clearance
        synergy = 1.0 + (self.drug.entanglement_degree * 0.8)

        return perm * synergy

    def optimize(self, time_window_hours: float = 8.0) -> CombinedProtocolResult:
        """
        Finds the optimal interval between LIPUS and drug administration.

        Returns:
            CombinedProtocolResult with optimal timing and predicted outcomes.
        """
        # Sample time points (0 to 8 hours post-LIPUS)
        times = np.linspace(0, time_window_hours, 1000)

        # Calculate absorption efficiency at each point
        efficiencies = np.array([self._absorption_efficiency(t) for t in times])

        # Find peak absorption time
        optimal_idx = np.argmax(efficiencies)
        optimal_time = times[optimal_idx]
        max_efficiency = efficiencies[optimal_idx]

        # Calculate clearance boost at optimal time
        clearance_boost = self._clearance_boost(optimal_time)

        # Determine tissue states for visualization
        tissue_states = []
        for t in np.linspace(0, 8, 17):  # Every 30 minutes
            if t < 2:
                state = TissueState.PRIMED
            elif t < 4:
                state = TissueState.PEAK_OPEN
            elif t < 6:
                state = TissueState.CLOSING
            else:
                state = TissueState.SEALED
            tissue_states.append((float(t), state.name))

        # Calculate safety margin (distance from dangerous MI levels)
        safety = 1.0 - (self.lipus.mi / 0.6)

        # Generate clinical recommendation
        recommendation = self._generate_recommendation(
            optimal_time, max_efficiency, clearance_boost, safety
        )

        return CombinedProtocolResult(
            optimal_interval_hours=float(optimal_time),
            predicted_absorption_efficiency=float(max_efficiency),
            clearance_boost_factor=float(clearance_boost),
            safety_margin=float(safety),
            tissue_states=tissue_states,
            recommendation=recommendation
        )

    def _generate_recommendation(
        self,
        optimal_time: float,
        efficiency: float,
        clearance: float,
        safety: float
    ) -> str:
        """Generates natural-language clinical recommendation."""

        if safety < 0.2:
            safety_warning = "⚠️ CAUTION: Mechanical Index near safety limit!"
        else:
            safety_warning = "✅ Safety parameters within normal range."

        if efficiency > 0.8:
            eff_quality = "EXCELLENT"
        elif efficiency > 0.5:
            eff_quality = "GOOD"
        else:
            eff_quality = "MODERATE"

        return (
            f"Combined Protocol Recommendation:\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Administer drug {optimal_time:.1f} hours post-LIPUS\n"
            f"• Predicted absorption: {eff_quality} ({efficiency:.1%})\n"
            f"• Clearance boost: {clearance:.2f}x baseline\n"
            f"• {safety_warning}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Philosophical note: 'As the pulse synchronizes the tissue, "
            f"the quantum and biological realms converge in the dance of healing.'"
        )
