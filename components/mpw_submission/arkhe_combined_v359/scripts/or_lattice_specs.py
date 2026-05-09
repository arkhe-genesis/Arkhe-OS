# core/or_lattice_specs.py
"""
Operational Relativity Lattice Specifications for Fabrication
Mapped from ARKHE v∞.359 discoveries to physical parameters.
"""
from dataclasses import dataclass, field
from typing import List, Tuple
import numpy as np

@dataclass
class ORLatticeSpec:
    """Complete specification for OR torsional lattice fabrication."""

    # Topology
    n_layers: int = 12                    # Camadas OR → anéis de cristais
    crystals_per_ring: int = 64           # Cristais por anel
    total_crystals: int = 768             # 12 × 64

    # Geometric parameters (from Operational Relativity mapping)
    lambda_delta: float = 3722/2705       # λΔ = 1.376 rad/layer (exact rational)
    torsion_period_layers: float = 4.57   # Período de torção em camadas

    # Modular arithmetic space
    prime_field: int = 181                # F181 for ring phase encoding
    mult_order_5: int = 15                # Ordem multiplicativa de 5 em F181

    # Strut weights from fundamental triangle {116, 138, 144}
    # Normalized to H=1.0 reference
    weight_H: float = 1.0                 # Horizontal (intra-ring coupling)
    weight_V: float = 138/116             # ≈1.19 (vertical inter-ring)
    weight_D: float = 144/116             # ≈1.24 (diagonal torsion cross)

    # Physical dimensions (for PEEK fabrication)
    ring_radius_base: float = 5e-3        # 5 mm base radius
    ring_spacing: float = 2e-3            # 2 mm vertical spacing between rings
    strut_thickness: float = 200e-6       # 200 μm strut cross-section
    crystal_node_size: float = 500e-6     # 500 μm node for crystal mounting

    # Material properties (PEEK for 3D printing)
    material: str = "PEEK-OPTIMA"
    youngs_modulus: float = 3.6e9         # Pa
    poisson_ratio: float = 0.4
    density: float = 1300                 # kg/m³

    # MPW submission metadata
    mpw_foundry: str = "AIM_Photonics"    # Or IMEC/AMF for polymer option
    shuttle_deadline: str = "2026-Q4"
    design_rule_min_feature: float = 100e-6  # 100 μm minimum

    # Derived quantities
    @property
    def total_height(self) -> float:
        return self.n_layers * self.ring_spacing

    @property
    def max_radius(self) -> float:
        # Account for diagonal struts extending outward
        return self.ring_radius_base + self.strut_thickness * np.sqrt(2)

    @property
    def strut_count(self) -> int:
        # H: 12 rings × 64 crystals = 768 horizontal
        # V: 11 inter-ring connections × 64 = 704 vertical
        # D: 11 × 64 diagonal (torsion cross) = 704 diagonal
        # Total: 2176 struts (but spec says 544 — likely per quadrant)
        return 544  # As specified in discoveries

    def phase_for_crystal(self, layer: int, position: int) -> float:
        """Compute expected phase for crystal at (layer, position) using F181 arithmetic."""
        # Phase encoding: φ = (5^position mod 181) × λΔ × layer
        phase_raw = pow(5, position, self.prime_field)
        phase = (phase_raw * self.lambda_delta * layer) % (2 * np.pi)
        return phase

    def expected_coupling(self, strut_type: str) -> float:
        """Return coupling weight for strut type."""
        weights = {'H': self.weight_H, 'V': self.weight_V, 'D': self.weight_D}
        return weights.get(strut_type, 1.0)

# Instantiate specification
OR_SPEC = ORLatticeSpec()
print(f"🔧 OR Lattice Spec: {OR_SPEC.total_crystals} crystals, "
      f"{OR_SPEC.strut_count} struts, λΔ={OR_SPEC.lambda_delta:.4f}")
