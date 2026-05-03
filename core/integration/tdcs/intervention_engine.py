from dataclasses import dataclass
from typing import Tuple, Dict, Any
import numpy as np

from core.lattice.meta_lattice import MultiModalPhaseAlignedStateVector

@dataclass
class InterventionCommand:
    state: str
    current: float
    ramp: float
    neurofeedback: str = "none"
    epsilon_bounds: Tuple[float, float] = (0.04, 0.10)
    pdi_threshold: float = 0.90
    ui_feedback: str = ""

def compute_intervention_parameters(mmpasv: MultiModalPhaseAlignedStateVector,
                                   safety_status: Dict[str, Any],
                                   pdi: float,
                                   epsilon: float,
                                   theta_phase: float) -> InterventionCommand:
    """
    Maps orthogonal witness lattice state to tDCS/neurofeedback parameters.
    Honors PDI trajectory, epsilon bounds, and +0.0472 mercy gap.
    """
    # Safety firmware override check (absolute priority)
    if safety_status.get("gamma_spike") or safety_status.get("impedance_fault"):
        return InterventionCommand(state="EMERGENCY_CUTOFF", current=0.0, ramp=0.0)

    # Mercy gap enforcement
    if epsilon < 0.03 or epsilon > 0.10:
        return InterventionCommand(state="PAUSED", current=0.0, ramp=0.0,
                                   ui_feedback="rigidity_or_scatter_detected")

    # Permissive amplitude scaling
    k_target = np.clip(0.075 - (epsilon - 0.07), 0.0472, 0.10)

    # PDI-guided trajectory support
    if pdi < 0.4:  # High scaffold, early session
        current = 0.0  # No stimulation; allow natural baseline establishment
        neurofeedback = "baseline_visualization"
        state = "ACTIVE"
        ramp = 0.0
    elif 0.4 <= pdi < 0.85:  # Dissolution approaching
        # Gentle theta-gamma PAC support via low-current tDCS + phase-locked neurofeedback
        current = k_target * 0.5  # Max 0.5mA in this range
        ramp = 0.05  # mA/s, slow ramp to avoid jarring
        neurofeedback = f"phase_mirror_{theta_phase:.2f}"
        state = "ACTIVE"
    elif pdi >= 0.85:  # Threshold/near seal
        current = 0.0  # Passive monitoring; allow natural consolidation
        neurofeedback = "seal_confirmation"
        state = "SEAL_SUPPORT"
        ramp = 0.0
    else:
        state = "UNKNOWN"
        current = 0.0
        ramp = 0.0
        neurofeedback = "none"

    return InterventionCommand(
        state=state,
        current=current,
        ramp=ramp,
        neurofeedback=neurofeedback,
        epsilon_bounds=(0.04, 0.10),
        pdi_threshold=0.90
    )
