import pytest
from catedrald_part2 import CatedralCore
from graphene_resonator import GrapheneSubstrate

def test_graphene_integration():
    core = CatedralCore()
    assert hasattr(core, 'graphene')
    assert isinstance(core.graphene, GrapheneSubstrate)

    state = core.get_full_state()
    assert 'graphene' in state
    assert state['graphene']['material'] == "Graphene (C)"
    assert 'axon_frequency' in state['graphene']
    assert 'valley_key_hash' in state['graphene']
    assert len(state['graphene']['valley_key_hash']) == 16

def test_graphene_anomaly():
    substrate = GrapheneSubstrate(strain=0.05)
    # Baseline is the same as current resonator
    assert substrate.sensor.detect_anomaly(substrate.resonator) == 0.0

    from graphene_resonator import GrapheneResonator
    # New resonator with different strain should have anomaly
    new_resonator = GrapheneResonator(strain_percent=0.1)
    anomaly = substrate.sensor.detect_anomaly(new_resonator)
    assert anomaly > 0.0
