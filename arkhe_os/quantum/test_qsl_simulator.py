import pytest
import numpy as np
from arkhe_os.quantum.qsl_simulator import KagomeQSLSimulator

def test_qsl_simulator_initialization():
    sim = KagomeQSLSimulator(n_unit_cells=2, J=1.0)
    assert sim.n == 2
    assert sim.N == 6
    assert len(sim.triangles) == 4

def test_qsl_simulator_non_commutativity():
    sim = KagomeQSLSimulator(n_unit_cells=2, J=1.0)
    non_comm = sim.non_commutativity_measure()
    assert non_comm > 0.0

def test_qsl_simulator_compute_coherence():
    sim = KagomeQSLSimulator(n_unit_cells=2, J=1.0)
    coherence = sim.compute_coherence()
    assert 0.0 <= coherence <= 1.0

def test_qsl_simulator_spinon_excitation():
    sim = KagomeQSLSimulator(n_unit_cells=2, J=1.0)
    k = np.array([np.pi, 0])
    spinon_state = sim.spinon_excitation(k)
    assert len(spinon_state) == 2**sim.N
    assert np.isclose(np.linalg.norm(spinon_state), 1.0)
