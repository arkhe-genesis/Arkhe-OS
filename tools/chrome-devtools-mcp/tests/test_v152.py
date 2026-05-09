import pytest
import sys
import os
sys.path.append(os.path.abspath('.'))

from scripts.arkhe_distributed_quantum_network_v152 import (
    ChronoCoilChip,
    DistributedQuantumNetwork,
    QuantumAISimulation
)

def test_chrono_coil_network():
    network = DistributedQuantumNetwork()
    network.add_node(ChronoCoilChip("ALPHA", 4, 12))
    network.add_node(ChronoCoilChip("BETA", 4, 15))
    network.add_link("ALPHA", "BETA", "GHZ", 0.97)

    fid_ab = network.simulate_teleportation("ALPHA", "BETA", ["ALPHA", "BETA"])
    assert round(fid_ab, 4) == 0.9226

def test_quantum_ai_simulation():
    ai_sim = QuantumAISimulation()
    acc, conf, err = ai_sim.simulate_zz_feature_map(12)
    assert acc == 0.60
    assert round(err, 4) == 0.0631
