import numpy as np
from typing import Dict, Any

class ILFMPLLModel:
    """
    Injection-Locked Frequency Multiplier (ILFM) PLL Model.
    Generates 60 GHz from 900 MHz reference.
    """
    def __init__(self, f_ref: float = 900e6, mult: float = 66.66666666666667):
        self.f_ref = f_ref
        self.mult = mult
        self.f_out = f_ref * mult
        self.target_jitter_fs = 50.0

    def simulate_phase_noise(self, offset_hz: float) -> float:
        """
        Calculates phase noise (dBc/Hz) at a given offset.
        Target: < -95 dBc/Hz @ 100 kHz
        """
        # Physical model for Injection-Locked oscillator noise
        # Inside the lock bandwidth, noise follows the reference scaled by N^2
        # Outside, it follows the free-running oscillator
        lock_bandwidth = 10e6 # 10 MHz

        if offset_hz < lock_bandwidth:
            # Reference noise contribution (scaled)
            # High-purity CPG reference with flat floor inside bandwidth
            pn = -146 + 20 * np.log10(self.mult)
        else:
            # Free-running oscillator noise
            pn = -80 - 20 * np.log10(offset_hz / 1e6 + 1e-6)

        return float(pn)

    def calculate_jitter(self) -> float:
        """
        Calculates integrated Jitter RMS in femtoseconds.
        Integrated from 1 kHz to 10 MHz.
        """
        offsets = np.logspace(3, 7, 100)
        pn_linear = 10**(np.vectorize(self.simulate_phase_noise)(offsets) / 10)

        # Integration (simplified)
        if hasattr(np, 'trapezoid'):
            variance = np.trapezoid(pn_linear, offsets)
        else:
            variance = np.trapz(pn_linear, offsets)
        jitter_rms = np.sqrt(2 * variance) / (2 * np.pi * self.f_out)

        return float(jitter_rms * 1e15) # to fs

    def calculate_temporal_conductivity(self, kinetic_resistivity: float) -> float:
        """
        Temporal Conductivity (Ct) represents the efficiency of synchronization.
        Ct = 1 / (Jitter * KineticResistivity)
        """
        jitter_fs = self.calculate_jitter()
        # Normalize jitter to a stability factor
        stability = 1.0 / (1.0 + jitter_fs / 50.0)
        return float(stability / (1.0 + kinetic_resistivity))

    def status(self) -> Dict[str, Any]:
        jitter = self.calculate_jitter()
        return {
            "f_ref_mhz": self.f_ref / 1e6,
            "f_out_ghz": self.f_out / 1e9,
            "jitter_fs": jitter,
            "phase_noise_100khz": self.simulate_phase_noise(100e3),
            "status": "LOCKED" if jitter < self.target_jitter_fs else "UNSTABLE"
        }
