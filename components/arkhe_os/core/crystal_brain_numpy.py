import numpy as np
from typing import Tuple

class VectorizedKuramoto:
    """Dinâmica de Kuramoto vetorizada com NumPy."""
    def __init__(self, n_oscillators: int, global_coupling: float):
        self.N = n_oscillators
        self.K = global_coupling
        self.phases = np.random.uniform(0, 2*np.pi, self.N)
        self.natural_frequencies = np.random.normal(0, 1.0, self.N)

    def step(self, dt: float = 0.01) -> np.ndarray:
        # Vectorized calculation: sin(phi_j - phi_i) for all i, j
        diffs = self.phases[None, :] - self.phases[:, None]
        coupling_term = np.sum(np.sin(diffs), axis=1) * (self.K / self.N)
        self.phases += dt * (self.natural_frequencies + coupling_term)
        self.phases = np.mod(self.phases, 2*np.pi)
        return self.phases

    def order_parameter(self) -> complex:
        return np.mean(np.exp(1j * self.phases))
