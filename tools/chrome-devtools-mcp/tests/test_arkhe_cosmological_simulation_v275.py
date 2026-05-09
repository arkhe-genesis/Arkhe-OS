import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.arkhe_cosmological_simulation_v275 import (
    DistributedCosmologicalSimulator,
    MPC_TO_M
)

def test_distributed_cosmological_simulation():
    universe_bounds = {
        'x': (0, 10 * MPC_TO_M),
        'y': (0, 10 * MPC_TO_M),
        'z': (0, 10 * MPC_TO_M),
    }

    simulator = DistributedCosmologicalSimulator(
        universe_bounds=universe_bounds,
        n_nodes=8,
        tvm_model_path=None
    )

    simulator.initialize_particles(particles_per_region=50, dark_fraction=0.85)

    final_stats = simulator.run_full_simulation(
        n_cosmological_steps=5,
        steps_per_report=1
    )

    assert final_stats['nodes_active'] == 8
    assert final_stats['final_global_coherence'] > 0
    assert final_stats['final_fingerprint_alignment'] > 0
