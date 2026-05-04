# core/morphogenesis/cell.py
"""
Cell — Mass-action receptor kinetics with stochastic fate decision.
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict

@dataclass
class CellState:
    position: np.ndarray  # (x, y, z) in cylindrical lattice
    layer: int            # z-index
    ring: int             # radial index (0 = axis, >0 = ring)
    bound_ratio: float = 0.0  # [0,1] fraction of occupied receptors
    fate: str = "UNDECIDED"
    division_probability: float = 0.0

class CellPopulation:
    """Manages cells with vectorized receptor kinetics."""
    def __init__(self, k_on: float = 1.0, k_off: float = 0.2, K_d: float = 0.5, hill_n: float = 3.0):
        self.k_on = k_on
        self.k_off = k_off
        self.K_d = K_d
        self.hill_n = hill_n
        self.cells = []  # List of CellState

    def add_cells(self, cells: list[CellState]):
        self.cells.extend(cells)

    def update_receptor_kinetics(self, extracellular_concentration: np.ndarray, dt: float):
        """
        Vectorized mass-action update: db/dt = k_on·c·(1-b) - k_off·b
        Closed-form solution for stability: b(t+dt) = b_ss + (b(t)-b_ss)e^{-(k_on·c + k_off)dt}
        """
        if not self.cells: return
        c_ext = np.array([cell.bound_ratio for cell in self.cells])  # placeholder mapping
        # Map cell.z to field index
        for i, cell in enumerate(self.cells):
            c = extracellular_concentration[cell.layer] if cell.layer < len(extracellular_concentration) else 0.0
            # Steady state and rate
            b_ss = c / (c + self.K_d)
            k_total = self.k_on * c + self.k_off
            cell.bound_ratio = b_ss + (cell.bound_ratio - b_ss) * np.exp(-k_total * dt)
            cell.bound_ratio = np.clip(cell.bound_ratio, 0.0, 1.0)

    def decide_fate_stochastic(self, rng: np.random.Generator, noise_sigma: float = 0.1):
        """Hill function + Langevin noise for fate decision."""
        for cell in self.cells:
            # Transcriptional response approximation
            response = cell.bound_ratio / (1e-6 + cell.bound_ratio)
            hill_val = 1.0 / (1.0 + (self.K_d / (cell.bound_ratio + 1e-6))**self.hill_n)
            # Add Gaussian noise (Langevin)
            noise = rng.normal(0.0, noise_sigma)
            effective_signal = hill_val + noise

            # Threshold-based fate
            if effective_signal > 0.7:
                cell.fate = "CAPTURE"  # Differentiate, stop dividing
                cell.division_probability = 0.0
            elif effective_signal < 0.3:
                cell.fate = "DILUTION"  # Proliferate
                cell.division_probability = 0.9
            else:
                cell.fate = "SHATTERING"  # Transitional/stochastic
                cell.division_probability = 0.4 * (1.0 + noise)
