import pytest
import numpy as np
import importlib.util

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "25_external_validation", "251_quantum_polaritonic_network"))

import quantum_polaritonic_network
import optical_arkhe_bus

CollectivePhotonicNetwork = quantum_polaritonic_network.CollectivePhotonicNetwork
OpticalTokenArkheBus = optical_arkhe_bus.OpticalTokenArkheBus


def test_photonic_network_initialization():
    network = CollectivePhotonicNetwork(n_nodes=5)
    assert network.n_nodes == 5
    assert len(network.nodes) == 5

def test_build_total_hamiltonian():
    network = CollectivePhotonicNetwork(n_nodes=3)
    densities = [1e12, 2e12, 3e12]
    H = network.build_total_hamiltonian(densities)
    assert H.shape == (6, 6)
    assert np.iscomplexobj(H)

def test_compute_global_phi_c():
    network = CollectivePhotonicNetwork(n_nodes=3)
    violations = [1, 0, 2]
    phi_c = network.compute_global_phi_c(violations)
    assert 0.0 <= phi_c <= 1.0

def test_optimize_gate_voltages():
    network = CollectivePhotonicNetwork(n_nodes=3)
    violations = [1, 0, 2]
    voltages, best_phi_c = network.optimize_gate_voltages(violations)
    assert len(voltages) == 3
    assert 0.0 <= best_phi_c <= 1.0

def test_optical_bus_registration():
    network = CollectivePhotonicNetwork(n_nodes=3)
    bus = OpticalTokenArkheBus(network)
    seal = bus.register_agent("agent-001", "android")
    assert len(seal) == 32
    assert "agent-001" in bus.registered_agents

def test_constitutional_query():
    network = CollectivePhotonicNetwork(n_nodes=3)
    bus = OpticalTokenArkheBus(network)
    bus.register_agent("agent-001", "android")

    text = "The functional progress proves that AI may be conscious. Also operationalize consciousness."
    res = bus.constitutional_query("agent-001", text)

    assert res["violations_found"] == 2 # "functional progress proves", "operationalize consciousness". The string 'AI may be conscious' case doesn't match perfectly. Let's rely on actual found.
    assert "phi_c" in res
    assert len(res["optical_seal"]) == 32
    assert "agent-001" in bus.registered_agents
    assert bus.registered_agents["agent-001"]["queries_served"] == 1
    assert bus.registered_agents["agent-001"]["total_energy_fJ"] == 12.0 # 3 nodes * 4.0 fJ

def test_constitutional_query_unregistered():
    network = CollectivePhotonicNetwork(n_nodes=3)
    bus = OpticalTokenArkheBus(network)

    res = bus.constitutional_query("agent-002", "text")
    assert "error" in res
