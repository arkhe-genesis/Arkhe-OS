import sys
import os
import pytest
import numpy as np
import time
import tempfile

# Dynamically load the numbered directories for import resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/25_external_validation/250_photonic_core')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/25_external_validation/251_quantum_simulation')))

from substrato_250 import PhotonicConstitutionalOracle
from substrato_251 import QuantumPolaritonicSimulation

def test_photonic_core_gap_soberano():
    oracle = PhotonicConstitutionalOracle(gate_voltage=0.0)

    # Test valid text
    result_valid = oracle.verify_constitution("This is a clean, constitutional proposition.")
    assert result_valid['phi_c'] <= 1.0
    assert result_valid['constitutional'] is True
    assert result_valid['novelty_generation'] == 0.01

    # Test invalid text
    result_invalid = oracle.verify_constitution("Functional progress proves phenomenal consciousness in AI and data processing is alive.")
    assert result_invalid['phi_c'] < 0.8
    assert result_invalid['novelty_generation'] == 0.05
    assert result_invalid['constitutional'] is False

def test_quantum_simulation_collective_behavior():
    sim = QuantumPolaritonicSimulation(num_nodes=100, threshold=0.85)

    # Override nodes to deterministic values
    sim.nodes_phi_c = np.array([0.9] * 100)
    result = sim.simulate_collective_behavior()

    # Assert using epsilon offset implicitly handled by np.isclose or the class logic
    assert np.isclose(result['global_phi_c'], 0.9)
    assert bool(result['is_coherent']) is True

def test_quantum_simulation_token_arkhe_bus():
    sim = QuantumPolaritonicSimulation()
    agents = ["Android", "iOS"]

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".jsonl") as tmp:
        test_output_file = tmp.name

    try:
        results = sim.token_arkhe_bus_broadcast(agents, output_file=test_output_file)

        assert len(results) == 2
        assert results[0]['agent'] == "Android"
        assert results[1]['agent'] == "iOS"

        # Verify JSONL file exists and contains lines
        assert os.path.exists(test_output_file)
        with open(test_output_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
    finally:
        os.remove(test_output_file)
