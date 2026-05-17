import pytest
from substrates.substrato_210_the_project_2_0 import ContinentalMind, ProtocolLayer

def test_continental_mind():
    mind = ContinentalMind(name="ARKHE_Continental_Mind_v1")
    neuron1 = mind.register_neuron("https://info.cern.ch", "128.141.201.200", ProtocolLayer.APPLICATION)
    neuron2 = mind.register_neuron("https://arkhe.cathedral", "10.0.0.1", ProtocolLayer.COGNITIVE)

    assert len(mind.neurons) == 2
    assert mind.total_synapses == 0

    mind.connect("https://info.cern.ch", "https://arkhe.cathedral", 10.0)
    assert mind.total_synapses == 1
    assert len(neuron1.axon_terminals) == 1
    assert len(neuron2.dendrites) == 1

    activated = mind.propagate_thought("https://info.cern.ch", 100.0)
    assert "https://arkhe.cathedral" in activated

    global_phi = mind.compute_global_phi_c()
    assert global_phi >= 0.0
