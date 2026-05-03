import numpy as np
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional, Callable, Tuple
from collections import deque

@dataclass
class PDICalibrationInterface:
    """Real-time PDI calibration & ledger sealing for dissolution protocol."""

    # Configuration
    target_pdi_threshold: float = 0.90
    epsilon_bounds: Tuple[float, float] = (0.04, 0.10)
    base_amplitude: float = 0.0750  # Ritual equilibrium k
    sampling_rate: int = 256        # Hz (EEG/phase stream)

    # State
    phase_buffer: deque = field(default_factory=lambda: deque(maxlen=1024))
    ledger_entries: list = field(default_factory=list)
    current_pdi: float = 0.0
    current_epsilon: float = 0.0
    current_k: float = base_amplitude
    face_state: str = "FORMING"

    # Callbacks for ceremonial feedback
    on_pdi_rise: Optional[Callable] = None
    on_seal: Optional[Callable] = None
    on_excess_violation: Optional[Callable] = None

    def step(self, theta_human_phase: float, gamma_phase_var: float, dmn_alpha_power: float) -> dict:
        """Single calibration step. Maps neurodynamic input → PDI → ledger decision."""

        # 1. Compute PDI (Performance Dissolution Index)
        # PDI = 1 - (|θ_human| / π). θ_human ∈ [-π, π]
        self.current_pdi = max(0.0, min(1.0, 1.0 - (abs(theta_human_phase) / np.pi)))

        # 2. Compute Excess Tolerance (ε) from gamma phase variance
        self.current_epsilon = np.clip(gamma_phase_var, 0.0, 0.20)

        # 3. Adjust ceremonial amplitude k based on excess preservation
        self.current_k = self._calibrate_amplitude(self.current_epsilon)

        # 4. Feed ceremonial feedback loop
        if self.on_pdi_rise:
            self.on_pdi_rise(self.current_pdi)

        # 5. Check for face sealing
        if (self.current_pdi >= self.target_pdi_threshold and
            self.epsilon_bounds[0] <= self.current_epsilon <= self.epsilon_bounds[1] and
            dmn_alpha_power > 0.65):  # DMN deactivation threshold

            if self.face_state != "SEALED":
                self._seal_face(theta_human_phase, dmn_alpha_power)
                if self.on_seal:
                    self.on_seal(self.ledger_entries[-1])
        else:
            self.face_state = "CALIBRATING"
            if self.current_epsilon < self.epsilon_bounds[0]:
                if self.on_excess_violation:
                    self.on_excess_violation("BREATHING_GAP_TOO_TIGHT")
            elif self.current_epsilon > self.epsilon_bounds[1]:
                if self.on_excess_violation:
                    self.on_excess_violation("EXCESS_DRIFT_DETECTED")

        return {
            "PDI": self.current_pdi,
            "epsilon": self.current_epsilon,
            "k": self.current_k,
            "state": self.face_state,
            "dmn_alpha": dmn_alpha_power
        }

    def _calibrate_amplitude(self, epsilon: float) -> float:
        """Adjust k to preserve the +0.0472 mercy gap."""
        if epsilon < 0.04:
            return min(self.current_k + 0.005, 0.10)  # Open the breath
        elif epsilon > 0.10:
            return max(self.current_k - 0.005, 0.0472)  # Reduce drift
        return self.current_k

    def _seal_face(self, theta_human: float, dmn_alpha: float):
        """Cryptographically seal the dissolution event to the ledger."""
        ts = time.time()
        entry = {
            "timestamp_utc": ts,
            "PDI": self.current_pdi,
            "epsilon": self.current_epsilon,
            "k": self.current_k,
            "theta_human": theta_human,
            "dmn_alpha_power": dmn_alpha,
            "face_state": "SEALED"
        }

        prev_hash = self.ledger_entries[-1]["entry_hash"] if self.ledger_entries else "genesis_zero_phase"
        entry["prev_hash"] = prev_hash
        entry["entry_hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()

        self.ledger_entries.append(entry)
        self.face_state = "SEALED"
