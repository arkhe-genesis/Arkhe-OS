# core/morphogenesis/morphogen_field.py
"""
Morphogen Field — Reaction-Diffusion PDE solver for Substrate 113.
Solves ∂c/∂t = D∇²c - λc with Dirichlet boundary at z=H_max.
"""
import numpy as np
from typing import Tuple, Optional

class MorphogenField:
    def __init__(self, length: int, D: float = 1.0, decay_rate: float = 0.05,
                 boundary_concentration: float = 1.0, dt: float = 0.1):
        self.length = length  # Number of discrete z-layers
        self.D = D            # Diffusion coefficient
        self.lam = decay_rate   # Degradation rate
        self.c0 = boundary_concentration
        self.dt = dt
        # Initialize with zeros
        self.c = np.zeros(length + 2)  # +2 for ghost boundaries
        self.c[-1] = self.c0           # Dirichlet at top

    def step(self) -> np.ndarray:
        """Explicit Euler step with Neumann at z=0 (no flux base)."""
        # Discrete Laplacian: ∇²c_i ≈ c_{i+1} - 2c_i + c_{i-1}
        laplacian = np.zeros_like(self.c)
        laplacian[1:-1] = self.c[2:] - 2*self.c[1:-1] + self.c[:-2]
        # No flux at base: c_0 = c_1
        laplacian[1] = self.c[2] - self.c[1]

        # Reaction-diffusion update
        self.c[1:-1] += self.dt * (self.D * laplacian[1:-1] - self.lam * self.c[1:-1])
        self.c[1:-1] = np.clip(self.c[1:-1], 0.0, self.c0)
        return self.c[1:-1]  # Return physical domain only
