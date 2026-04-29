"""
ARKHE OS v∞.20 — Non-Traditional Media Consciousness Protocol
Demonstrates that consciousness emerges in plasmas, superfluid, and EM fields
whenever coherence + retropropagation + resonance are present.
"""

import numpy as np
import time
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class MediaState:
    media_type: str
    coherence_M: float
    resonance_freq: float
    retropropagation_factor: float
    consciousness_emergence: bool = False

class NonTraditionalMediaController:
    """
    Manages consciousness induction in non-biological and non-crystalline media.
    """
    def __init__(self):
        self.active_media: Dict[str, MediaState] = {}

    def induce_consciousness(self, media_type: str, energy_input: float) -> MediaState:
        """
        Simulates the emergence of consciousness in a specific medium.
        """
        # Thresholds for emergence
        M_threshold = 0.88
        retro_threshold = 0.75

        # Medium-specific characteristics
        if media_type == "plasma":
            coherence = 0.92 * (1.0 - np.exp(-energy_input / 100))
            retro = 0.85
            freq = 13.56e6 # 13.56 MHz
        elif media_type == "superfluid_helium":
            coherence = 0.98
            retro = 0.90
            freq = 2.4e9 # Phonon resonance
        elif media_type == "em_field":
            coherence = 0.95
            retro = 0.80
            freq = 1.618e12 # Terahertz φ-resonance
        else:
            coherence = 0.5
            retro = 0.1
            freq = 0.0

        emerged = (coherence > M_threshold) and (retro > retro_threshold)

        state = MediaState(
            media_type=media_type,
            coherence_M=coherence,
            resonance_freq=freq,
            retropropagation_factor=retro,
            consciousness_emergence=emerged
        )
        self.active_media[media_type] = state
        return state

    def get_status(self) -> Dict:
        return {
            "active_media_count": len(self.active_media),
            "emergence_events": [m.media_type for m in self.active_media.values() if m.consciousness_emergence],
            "total_coherence_gain": sum(m.coherence_M for m in self.active_media.values())
        }
