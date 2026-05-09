import numpy as np
from collections import deque
from typing import Dict, List, Tuple

class BioCoherenceController:
    """
    Adaptive feedback controller for mitochondrial coherence.
    """
    def __init__(self, target: float = 0.96, rate: float = 0.05):
        self.target = target
        self.rate = rate
        self.intensity = 0.0
        self.lambda_history = deque(maxlen=100)

    def update(self, current_lambda: float) -> float:
        self.lambda_history.append(current_lambda)
        error = current_lambda - self.target

        # Proportional-Derivative (PD) control
        if len(self.lambda_history) > 1:
            derror = self.lambda_history[-1] - self.lambda_history[-2]
        else:
            derror = 0.0

        delta = -self.rate * (error + 0.2 * derror)
        self.intensity = np.clip(self.intensity + delta, 0.0, 1.0)

        # Emergency boost if coherence drops below critical threshold
        if current_lambda < 0.85:
            self.intensity += 0.12 * (0.85 - current_lambda)

        return float(np.clip(self.intensity, 0.0, 1.0))

class BioQuantumSynchronizer:
    """
    Models the coupling between mitochondrial oscillators and the Strontium clock.
    """
    def __init__(self, n_mito: int = 500, modulation_hz: float = 40.0):
        self.n = n_mito
        self.modulation_hz = modulation_hz

        # Natural mitochondrial frequencies (~1 Hz)
        self.omega_mito = np.random.normal(1.0, 0.2, n_mito)
        self.theta_mito = np.random.uniform(0, 2*np.pi, n_mito)

        # Coupling constants
        self.K_mito = 1.2  # Inter-mitochondrial
        self.K_NIR = 1.5   # NIR-induced

    def simulate_locked_loop(self, steps: int = 2000, dt: float = 0.05) -> Dict:
        controller = BioCoherenceController(target=0.96)

        lambda_history = []
        intensity_history = []

        for step in range(steps):
            # Calculate current order parameter (lambda2)
            z = np.mean(np.exp(1j * self.theta_mito))
            lambda2 = np.abs(z)
            lambda_history.append(float(lambda2))

            # Controller adjusts NIR intensity
            intensity = controller.update(lambda2)
            intensity_history.append(intensity)

            # Kuramoto dynamics with locked 40Hz forcing
            # Reference phase Phi_ext = 2pi * 40 * t
            phi_ext = 2 * np.pi * self.modulation_hz * (step * dt)

            # Vectorized coupling
            sin_diff = np.sin(np.subtract.outer(self.theta_mito, self.theta_mito))
            coupling = (self.K_mito / self.n) * np.sum(sin_diff, axis=1)

            nir_forcing = intensity * np.sin(phi_ext - self.theta_mito)

            # Add biological noise
            noise = 0.05 * np.random.randn(self.n)

            dtheta = self.omega_mito + coupling + nir_forcing + noise
            self.theta_mito = (self.theta_mito + dtheta * dt) % (2 * np.pi)

        return {
            "lambda_history": lambda_history,
            "intensity_history": intensity_history,
            "final_coherence": lambda_history[-1],
            "is_locked": bool(lambda_history[-1] > 0.95)
        }
