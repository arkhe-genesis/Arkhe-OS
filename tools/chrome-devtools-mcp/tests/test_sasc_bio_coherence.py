import pytest
import numpy as np
from src.physics.bio_coherence import BiophotonCoherenceSensor

def test_biophoton_sensor():
    sensor = BiophotonCoherenceSensor()
    # Coherent signal (Poisson)
    counts = np.random.poisson(100, 100)
    res = sensor.measure_coherence(counts, np.arange(100))
    assert res["lambda2_biophoton"] > 0
    assert "intensity" in res
    assert "g2_zero" in res

def test_biophoton_states():
    sensor = BiophotonCoherenceSensor()
    # High coherence (Sub-Poissonian)
    counts = np.random.normal(1000, 5, 100)
    res = sensor.measure_coherence(counts, np.arange(100))
    assert res["status"] == "SUPER_RADIANCE_TZINOR"
    assert res["g2_zero"] < 1.0
