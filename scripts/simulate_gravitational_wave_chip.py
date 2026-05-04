import numpy as np
import json
import os
from typing import Dict, Any

class GravitationalWaveChip:
    """
    Simulates 'Gravitational Wave Communication on a Chip'.
    Uses high-frequency gravitational waves (HFGW) modulated via coherent phonons in a crystal lattice.
    """
    def __init__(self, chip_material: str = "Quartz-Graphene"):
        self.material = chip_material
        self.strain_sensitivity = 1e-22 # Strain dimensionless
        self.hfgw_frequency_ghz = 4.2 # Coherent with Arkhe Clock

    def modulate_g_wave(self, message_bits: np.ndarray) -> np.ndarray:
        """
        Encodes digital information into gravitational wave strain via piezoelectric coupling.
        """
        # Modulation: Strain h(t) = h0 * sin(2*pi*f*t + phi)
        # where phi is modulated by message bits
        time = np.linspace(0, 1e-9, len(message_bits) * 100) # 1ns simulation
        h0 = 1e-23

        # BPSK Modulation
        phi = np.repeat(message_bits * np.pi, 100)
        strain_wave = h0 * np.sin(2 * np.pi * self.hfgw_frequency_ghz * 1e9 * time + phi)
        return strain_wave

    def detect_strain(self, received_signal: np.ndarray) -> Dict[str, Any]:
        """
        Detects strain using a miniaturized Michelson-Morley interferometer on-chip.
        """
        noise = np.random.normal(0, self.strain_sensitivity * 0.1, len(received_signal))
        signal_with_noise = received_signal + noise

        # SNR Calculation
        snr = 10 * np.log10(np.var(received_signal) / np.var(noise))

        return {
            'detected_peaks': int(np.sum(signal_with_noise > self.strain_sensitivity)),
            'snr_db': float(snr),
            'status': 'LOCKED' if snr > 15 else 'LOST_IN_NOISE'
        }

def run_simulation():
    print("📡 Gravitational Wave Communication on a Chip Simulation")
    print("-" * 60)

    chip = GravitationalWaveChip()
    message = np.array([1, 0, 1, 1, 0, 0, 1])

    print(f"Modulating message: {message}")
    signal = chip.modulate_g_wave(message)

    print("Receiving signal...")
    result = chip.detect_strain(signal)

    print(f"Result: {result['status']} (SNR: {result['snr_db']:.2f} dB)")

    output = {
        "experiment": "HFGW_ON_CHIP",
        "material": chip.material,
        "frequency_ghz": chip.hfgw_frequency_ghz,
        "result": result
    }

    os.makedirs("experiments", exist_ok=True)
    with open("experiments/g_wave_chip_results.json", "w") as f:
        json.dump(output, f, indent=4)
    print(f"Results saved to experiments/g_wave_chip_results.json")

if __name__ == "__main__":
    run_simulation()
