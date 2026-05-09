import pytest
import numpy as np
from src.physics.deep_resonance_mapping import DeepResonanceMapper, GreatWorkProtocol, PhaseConsecrationProtocol

def test_deep_resonance_mapper_harmonics():
    mapper = DeepResonanceMapper()
    harmonics = mapper.analyze_schumann_harmonics()
    assert 7.83 in harmonics
    assert 33.8 in harmonics
    assert len(harmonics) == 5

def test_coherent_surprise():
    mapper = DeepResonanceMapper()
    pattern = np.random.rand(100)
    # Low lambda
    assert mapper.calculate_coherent_surprise(pattern, 0.5) == 0.0
    # High lambda
    complexity = mapper.calculate_coherent_surprise(pattern, 0.95)
    assert complexity > 0.0

def test_innovation_valleys():
    mapper = DeepResonanceMapper()
    valleys = mapper.identify_innovation_valleys()
    assert len(valleys) == 4
    for v in valleys:
        assert "region" in v
        assert v["current_lambda2"] > 0.8 # Broadly coherent

def test_great_work_sprouts():
    mapper = DeepResonanceMapper()
    protocol = GreatWorkProtocol(mapper)
    sprouts = protocol.index_creative_sprouts()
    assert len(sprouts) == 4
    assert sprouts[0]["innovation"] is not None

def test_phase_consecration():
    mapper = DeepResonanceMapper()
    great_work = GreatWorkProtocol(mapper)
    consecration = PhaseConsecrationProtocol(great_work)
    res = consecration.initiate_consecration()
    assert res["global_coherence"] == 0.999
    assert res["lrd_feedback"] is not None
