import pytest
import numpy as np
from substrates.v174_hodge_duality import CoherenceManifoldConfig, DiscreteHodgeOperator, DiracTorsionSolver, QuantumSystemConfig, QuantumHodgeDuality, HarmonicCathedralAnalyzer

def test_hodge_duality():
    config = CoherenceManifoldConfig(
        dim=2, # Using 2 for easier testing
        n_vertices=16,
        metric_type='fisher_rao',
        torsion_strength=2.04,
        boundary_conditions='periodic'
    )
    hodge = DiscreteHodgeOperator(config)
    assert hodge.dim == 2

    solver = DiracTorsionSolver(hodge)
    result = solver.solve_zero_modes(tolerance=1e-8)
    assert result['found']

    q_config = QuantumSystemConfig(n_qubits=2)
    qhd = QuantumHodgeDuality(q_config)
    bell_projector = np.zeros((4, 4), dtype=complex)
    bell_projector[0, 0] = 0.5
    bell_projector[3, 3] = 0.5
    bell_projector[0, 3] = 0.5
    bell_projector[3, 0] = 0.5
    dual_op = qhd.hodge_dual_operator(bell_projector)
    invariance = qhd.verify_trace_invariance(bell_projector, bell_projector)
    assert invariance['invariant']

    analyzer = HarmonicCathedralAnalyzer(hodge)
    report = analyzer.generate_harmonic_report()
    assert report is not None
