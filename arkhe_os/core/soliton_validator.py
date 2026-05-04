"""
ARKHE OS v64.1 — SIMULAÇÃO COM VALIDAÇÃO CRIPTOGRÁFICA
Detecção de Fibonacci, compromisso ZK, exportação federada
"""

import numpy as np
import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from scipy.signal import find_peaks

@dataclass
class EmergentPatternProof:
    """Prova criptográfica de padrão emergente na simulação"""
    simulation_id: str
    timestamp_ns: int
    fibonacci_modes_detected: List[float]
    spectral_peak_significance: float
    pattern_commitment: str
    zkp_ready: bool

    def generate_commitment(self, psi_field: np.ndarray) -> str:
        """Gera compromisso criptográfico do campo Ψ"""
        field_hash = hashlib.sha256(
            np.abs(psi_field).tobytes() +
            np.angle(psi_field).tobytes()
        ).hexdigest()
        return f"0x{field_hash}"

class FibonacciModeDetector:
    """Detecta modos de Fibonacci no espectro de potência"""

    def __init__(self, k_vector: np.ndarray, L: float, phi: float = None):
        self.k = k_vector
        self.L = L
        self.phi = phi or (1 + np.sqrt(5)) / 2
        self.tolerance = 0.15

    def generate_fibonacci_sequence(self, k_min: float, k_max: float) -> List[float]:
        modes = []
        # Standard k_0 for N=512, L=100 is 2*pi/L
        k_0 = 2 * np.pi / self.L
        for n in range(-15, 15):
            # Try both positive and negative powers
            k_fib1 = k_0 * (self.phi ** float(n))
            k_fib2 = k_0 * (self.phi ** float(-n))
            for kf in [k_fib1, k_fib2]:
                if 0.01 <= abs(kf) <= 100.0:
                    modes.append(kf)
        return list(set(modes))

    def detect_modes(self, power_spectrum: np.ndarray, significance_threshold: float = 0.00001) -> List[Dict]:
        k_abs = np.abs(self.k)
        # Sort power spectrum to find peaks better
        peaks, _ = find_peaks(power_spectrum, height=significance_threshold * np.max(power_spectrum))
        fib_modes = self.generate_fibonacci_sequence(np.min(k_abs), np.max(k_abs))
        detected = []

        for peak_idx in peaks:
            k_peak = k_abs[peak_idx]
            if k_peak < 1e-6: continue # Skip DC component
            peak_power = power_spectrum[peak_idx]

            for k_fib in fib_modes:
                k_fib_abs = abs(k_fib)
                if k_fib_abs < 1e-6: continue
                if abs(k_peak - k_fib_abs) / k_fib_abs < self.tolerance:
                    detected.append({
                        'k_observed': float(k_peak),
                        'k_fibonacci': float(k_fib),
                        'relative_error': float(abs(k_peak - k_fib) / k_fib),
                        'power': float(peak_power),
                        'significance': float(peak_power / np.std(power_spectrum))
                    })
                    break

        return sorted(detected, key=lambda x: x['significance'], reverse=True)

class SolitonValidator:
    def __init__(self, L: float, phi: float = None):
        self.L = L
        self.phi = phi

    def validate_and_generate_proof(self, simulation_id: str, Psi: np.ndarray, k: np.ndarray) -> Dict:
        power_spectrum = np.abs(np.fft.fft(Psi))**2
        detector = FibonacciModeDetector(k, self.L, self.phi)
        detected_modes = detector.detect_modes(power_spectrum)

        proof = EmergentPatternProof(
            simulation_id=simulation_id,
            timestamp_ns=time.time_ns(),
            fibonacci_modes_detected=[m['k_fibonacci'] for m in detected_modes[:5]],
            spectral_peak_significance=detected_modes[0]['significance'] if detected_modes else 0.0,
            pattern_commitment="",
            zkp_ready=len(detected_modes) >= 3
        )
        proof.pattern_commitment = proof.generate_commitment(Psi)

        return {
            'proof': asdict(proof),
            'detected_modes': detected_modes,
            'stats': {
                'mean_density': float(np.mean(np.abs(Psi)**2)),
                'max_density': float(np.max(np.abs(Psi)**2)),
                'coherence': float(np.abs(np.mean(Psi))**2 / np.mean(np.abs(Psi)**2))
            }
        }
