from typing import Dict, Any
from core.multi_modal.orthogonal_witness import MultiModalPhaseAlignedStateVector

class OrthogonalInterventionMapper:
    """Maps the orthogonal witness state to personalized tDCS/neurofeedback parameters."""

    def __init__(self):
        self.target_epsilon_min = 0.04
        self.target_epsilon_max = 0.10
        self.base_intensity_ma = 1.0  # Baseline tDCS intensity in milliamperes
        self.max_intensity_ma = 2.0   # Maximum safe intensity

    def map_witness_to_stimulation(self, witness_state: MultiModalPhaseAlignedStateVector) -> Dict[str, Any]:
        """
        Converts phase coherence metrics (pdi_multi, epsilon_multi) into
        personalized tDCS parameters (intensity, frequency, phase offset).
        """
        response = {
            "timestamp": witness_state.relative_timestamp,
            "target_region": "Pz/Cz",  # Default to default mode network integration region
            "action": "HOLD_STEADY",
            "intensity_ma": self.base_intensity_ma,
            "phase_offset_adjustment": 0.0
        }

        # Adapt intensity based on multi-modal PDI (Performance Dissolution Index)
        # Higher dissolution (approaching 1.0) generally warrants maintaining or gently enhancing the state
        if witness_state.pdi_multi > 0.8:
            response["intensity_ma"] = min(self.base_intensity_ma * 1.2, self.max_intensity_ma)
            response["action"] = "ENHANCE_DISSOLUTION"
        elif witness_state.pdi_multi < 0.3:
            response["intensity_ma"] = self.base_intensity_ma * 0.8
            response["action"] = "GENTLE_RECOVERY"

        # Adapt phase offsets/stimulation style based on inter-modality variance (epsilon_multi)
        # The goal is to preserve the "mercy gap" (orthogonality), keeping epsilon within [0.04, 0.10]
        if witness_state.epsilon_multi > self.target_epsilon_max:
            # Too much variance (drifting apart) -> apply cohesive stimulation to bring them closer
            response["action"] = "DRIFT_CORRECTION"
            response["phase_offset_adjustment"] = -0.05  # Drive phase difference down
            # Increase intensity slightly to encourage coherence
            response["intensity_ma"] = min(response["intensity_ma"] * 1.1, self.max_intensity_ma)

        elif witness_state.epsilon_multi < self.target_epsilon_min:
            # Too little variance (rigid synchronization) -> apply orthogonalizing stimulation to restore the gap
            response["action"] = "RIGIDITY_OPENING"
            response["phase_offset_adjustment"] = +0.05  # Drive phase difference up (restore orthogonality)
            # Reduce intensity slightly or shift to alternating current (tACS) at orthogonal frequencies
            response["intensity_ma"] = max(response["intensity_ma"] * 0.9, 0.5)
            response["stimulation_type"] = "tACS_ORTHOGONAL"

        return response
