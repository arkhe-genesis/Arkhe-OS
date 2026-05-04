# core/morphogenesis/cylinder_growth.py
"""
Cylindrical Growth — Hexagonal packing with PDE morphogen gradient.
"""
import numpy as np
from typing import List, Tuple
from core.morphogenesis.cell import CellPopulation, CellState
from core.morphogenesis.morphogen_field import MorphogenField

def generate_hex_layer(z: int, radius: int) -> List[CellState]:
    """Generate cells in hexagonal close-packing for a single z-layer."""
    cells = []
    # Axis cell
    cells.append(CellState(position=np.array([0.0, 0.0, z]), layer=z, ring=0))
    if radius >= 1:
        # Rings
        for r in range(1, radius + 1):
            n_cells = 6 * r
            for k in range(n_cells):
                theta = 2 * np.pi * k / n_cells
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                cells.append(CellState(position=np.array([x, y, z]), layer=z, ring=r))
    return cells

class MorphogeneticCylinder:
    def __init__(self, height_max: int = 10, radial_layers: int = 2,
                 D: float = 1.0, decay: float = 0.08, dt: float = 0.1):
        self.height_max = height_max
        self.radial_layers = radial_layers
        self.dt = dt
        self.population = CellPopulation(k_on=2.0, k_off=0.5, K_d=0.3, hill_n=3.0)
        self.field = MorphogenField(length=height_max + 1, D=D, decay_rate=decay, dt=dt)
        self.rng = np.random.default_rng(42)

        # Seed base layer (z=0)
        self.population.add_cells(generate_hex_layer(0, radial_layers))

    def step(self) -> dict:
        """Execute one growth cycle: PDE → Receptor → Fate → Division."""
        # 1. Diffuse morphogen
        c_profile = self.field.step()

        # 2. Update receptor binding
        self.population.update_receptor_kinetics(c_profile, self.dt)

        # 3. Stochastic fate decision
        self.population.decide_fate_stochastic(self.rng, noise_sigma=0.15)

        # 4. Cell division & growth
        new_cells = []
        for cell in self.population.cells:
            if cell.fate == "DILUTION" and cell.division_probability > self.rng.random():
                if cell.position[2] < self.height_max:
                    # Divide: daughter above, same radial index
                    daughter_pos = cell.position.copy()
                    daughter_pos[2] += 1.0
                    new_cells.append(CellState(position=daughter_pos, layer=int(daughter_pos[2]),
                                               ring=cell.ring))
                    # Radial expansion if needed (simplified)
                    if cell.ring < self.radial_layers and cell.layer == int(daughter_pos[2]) - 1:
                        # Add ring expansion cell
                        new_r = cell.ring + 1
                        theta = 2 * np.pi * self.rng.integers(0, 6*new_r) / (6*new_r)
                        new_cells.append(CellState(position=np.array([new_r*np.cos(theta),
                                                                    new_r*np.sin(theta),
                                                                    daughter_pos[2]]),
                                                   layer=int(daughter_pos[2]), ring=new_r))

        self.population.add_cells(new_cells)

        # Metrics
        layers = set(c.layer for c in self.population.cells)
        fates = {}
        for cell in self.population.cells:
            fates[cell.fate] = fates.get(cell.fate, 0) + 1

        return {
            "cycle_cells": len(self.population.cells),
            "max_height": max(layers) if layers else 0,
            "fates": fates,
            "gradient_norm": np.linalg.norm(c_profile)
        }
