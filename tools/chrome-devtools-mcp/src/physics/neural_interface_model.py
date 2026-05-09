import numpy as np
from typing import Dict, Any

class NeuralInterfaceModel:
    """
    Models the sensory feedback loop (Haptic/Audio) for the External Hub.
    Maps the swarm order parameter R (coherence) to human-perceptible stimuli.
    """
    def __init__(self):
        self.r_threshold_high = 0.95
        self.r_threshold_low = 0.30
        self.base_haptic_freq = 7.35 # Hz (Schumann Resonance)
        self.base_audio_freq = 432.0 # Hz (Standard Healing Pitch)

    def calculate_haptic_feedback(self, R: float) -> Dict[str, float]:
        """
        Calculates vibrotactile parameters based on coherence R.
        """
        # Low coherence: Chaotic, irregular pulses
        # High coherence: Steady, sub-harmonic pulse
        if R > self.r_threshold_high:
            intensity = 0.8
            frequency = self.base_haptic_freq
            pattern = "STEADY_PULSE"
        elif R < self.r_threshold_low:
            intensity = 0.3 * np.random.random()
            frequency = 20.0 + 10.0 * np.random.random()
            pattern = "CHAOTIC_JITTER"
        else:
            # Linear transition
            t = (R - self.r_threshold_low) / (self.r_threshold_high - self.r_threshold_low)
            intensity = 0.3 + 0.5 * t
            frequency = 20.0 - (20.0 - self.base_haptic_freq) * t
            pattern = "STABILIZING_RHYTHM"

        return {
            "intensity_0to1": float(intensity),
            "frequency_hz": float(frequency),
            "pattern_type": pattern
        }

    def calculate_audio_feedback(self, R: float) -> Dict[str, Any]:
        """
        Maps coherence to binaural beat frequencies.
        """
        if R > 0.9:
            binaural_beat = 7.83 # Theta/Alpha border
            base_carrier = 432.0
            timbre = "SINE_HARMONIC"
        else:
            binaural_beat = 15.0 + (1.0 - R) * 20.0 # High Beta (Stress)
            base_carrier = 440.0
            timbre = "SAWTOOTH_LOWPASS"

        return {
            "carrier_hz": float(base_carrier),
            "beat_hz": float(binaural_beat),
            "timbre": timbre,
            "volume_db": -20.0 + 20.0 * R
        }

    def status(self, R: float) -> Dict[str, Any]:
        return {
            "order_parameter_R": R,
            "haptic": self.calculate_haptic_feedback(R),
            "audio": self.calculate_audio_feedback(R),
            "visual_color": "SAPPHIRE_BLUE" if R > 0.9 else "AMBER_WARNING" if R > 0.5 else "CRIMSON_CHAOS"
        }

if __name__ == "__main__":
    interface = NeuralInterfaceModel()

    # Simulate Coherence Transition
    for r in [0.2, 0.6, 0.98]:
        print(f"\n--- Coherence R = {r} ---")
        print(interface.status(r))
