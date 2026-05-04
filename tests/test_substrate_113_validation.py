# tests/test_substrate_113_validation.py
import pytest
import numpy as np
from core.morphogenesis.cylinder_growth import MorphogeneticCylinder
from core.morphogenesis.morphogen_field import MorphogenField
from core.morphogenesis.topological_encoding import MorphogenBraid

def test_cylinder_grows_to_target_height():
    sim = MorphogeneticCylinder(height_max=3, radial_layers=1, D=2.0, decay=0.05, dt=0.1)
    for _ in range(15):  # Allow 15 cycles
        sim.step()
    layers = set(c.layer for c in sim.population.cells)
    assert max(layers) == 3, f"Expected height 3, got {max(layers)}"
    assert len(sim.population.cells) >= 7, "Cylinder should have expanded radially+vertically"

def test_pde_vs_discrete_concentration_profile():
    field = MorphogenField(length=20, D=1.5, decay_rate=0.1, boundary_concentration=1.0, dt=0.05)
    for _ in range(500): field.step()
    c_discrete = field.c[1:-1]

    # Compare with exponential decay steady state: c(z) = c₀ e^{-√(λ/D)(H-z)}
    z = np.arange(1, 21)
    c_analytic = np.exp(-np.sqrt(field.lam/field.D) * (21 - z))

    # L2 error should be < 5% after sufficient steps
    error = np.linalg.norm(c_discrete - c_analytic) / np.linalg.norm(c_analytic)
    assert error < 0.05, f"Discrete-analytic error too high: {error:.3f}"

def test_fibonacci_trace_isomorphism():
    braid = MorphogenBraid("auxin", topological_charge=2)
    trace = braid.compute_fibonacci_trace()
    expected = ((np.sqrt(5)-1)/2)**2 + ((np.sqrt(5)+1)/2)**2  # φ² + φ⁻² = 3
    assert np.isclose(trace.real, 3.0, atol=1e-6)
    assert isinstance(braid.isomorphic_note(), str)
