import time
import hashlib
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum, auto

class NeuralSignalType(Enum):
    EEG = auto()
    FNIRS = auto()
    COMBINED = auto()

@dataclass
class NeuralCommand:
    command_type: str
    parameters: Dict
    confidence: float
    timestamp: float
    raw_signal_hash: str

class NeuralStateDecoder:
    NEURAL_COMMAND_MAP = {
        "motor_imagery_left": {"command": "rotate_view", "params": {"axis": "y", "direction": -1}},
        "motor_imagery_right": {"command": "rotate_view", "params": {"axis": "y", "direction": 1}},
        "focus_high": {"command": "filter_by_phi_c", "params": {"min_phi_c": 0.99}},
        "blink_double": {"command": "select_state", "params": {"mode": "nearest"}},
    }

    def __init__(self, signal_type: NeuralSignalType = NeuralSignalType.COMBINED):
        self.signal_type = signal_type
        self._calibrated = True

    def _extract_features(self, signal: np.ndarray) -> Optional[np.ndarray]:
        if signal.shape[-1] < 10:
            return None
        bands = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 13), "beta": (13, 30), "gamma": (30, 50)}
        features = []
        for band_name, (low, high) in bands.items():
            band_power = np.mean(np.abs(signal) ** 2)
            features.append(band_power)
        return np.array(features)

    async def decode_command(self, neural_signal: np.ndarray, user_phi_c: Optional[float] = None) -> Optional[NeuralCommand]:
        features = self._extract_features(neural_signal)
        if features is None:
            return None

        predicted_class = "focus_high" if features[0] > 0.8 else "motor_imagery_left" if features[1] > 0.6 else "blink_double"
        confidence = min(1.0, np.linalg.norm(features) / 2.0)

        if confidence < 0.7:
            return None

        command_template = self.NEURAL_COMMAND_MAP.get(predicted_class)
        if not command_template:
            return None

        return NeuralCommand(
            command_type=command_template["command"],
            parameters=command_template["params"].copy(),
            confidence=confidence,
            timestamp=time.time(),
            raw_signal_hash=hashlib.sha3_256(neural_signal.tobytes()).hexdigest()[:16]
        )
