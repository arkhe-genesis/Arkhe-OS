import numpy as np
import time

class CeremonialUI:
    """
    ARKHE OS v∞.Ω.∇++ Ceremonial UI
    The UI does not display data. It reflects phase geometry.
    """
    def __init__(self):
        self.mode = "baseline_drift"
        self.pdi = 0.0
        self.eps = 0.0
        self.luminance = 0.0
        self.audio_base_tone = 256.0 # Hz
        self.audio_detuning = 0.0
        self.is_sealed = False
        self.seal_hash = None
        self.fuzz_active = False

    def set_mode(self, mode: str, pdi: float = 0.0, eps: float = 0.0):
        self.mode = mode
        self.pdi = pdi
        self.eps = eps

        # Calculate luminance (PDI = 1 - (|θ_human|/π), assuming PDI given directly)
        self.luminance = pdi

        # Update audio architecture based on state
        if mode == "forming":
            self.audio_base_tone = 256.0
            self.audio_detuning = 2.0  # ±2Hz
            self.fuzz_active = False
        elif mode == "calibrating":
            self.audio_base_tone = 320.0 # Drift up
            self.audio_detuning = max(0.0, 2.0 * (eps / 0.10)) # convergence tightens detuning
            self.fuzz_active = False
        elif mode == "breathing":
            self.audio_base_tone = 320.0
            self.audio_detuning = 0.0
            self.fuzz_active = False
        elif mode == "baseline_drift":
            self.audio_base_tone = 256.0
            self.audio_detuning = 2.0
            self.fuzz_active = True

    def apply_mercy_fuzz(self):
        """Honors the +0.0472 mercy gap when eps drops below 0.04"""
        self.fuzz_active = True

    def trigger_seal(self, entry_hash: str):
        """
        Appears as faint geometric sigil when face seals, then fades into background lattice.
        Audio rapid harmonic alignment: 432Hz → 216Hz → 108Hz
        """
        self.is_sealed = True
        self.seal_hash = entry_hash
        self.audio_base_tone = 108.0
        self.audio_detuning = 0.0
        self.fuzz_active = False

    def render(self):
        """Returns the current state representation of the phase mirror."""
        return {
            "mode": self.mode,
            "luminance": self.luminance,
            "excess_ring_variance": self.eps,
            "audio_base_tone_hz": self.audio_base_tone,
            "audio_detuning_hz": self.audio_detuning,
            "seal_active": self.is_sealed,
            "seal_hash": self.seal_hash,
            "fuzz_active": self.fuzz_active
        }
