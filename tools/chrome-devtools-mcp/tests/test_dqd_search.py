import pytest
import numpy as np
from src.physics.dqd_search_sim import StanzaDQDSimulator

def test_device_health_check():
    sim = StanzaDQDSimulator("TEST-01")
    # Health check is probabilistic, but we can check if it sets bounds on success
    result = sim.device_health_check()
    if result:
        assert sim.is_healthy is True
        assert sim.v_bounds == (0.0, 2500.0)
    else:
        assert sim.is_healthy is False

def test_compute_peak_spacing_requires_health():
    sim = StanzaDQDSimulator("TEST-02")
    sim.is_healthy = False
    spacing = sim.compute_peak_spacing()
    assert spacing is None

def test_grid_search_requires_spacing():
    sim = StanzaDQDSimulator("TEST-03")
    sim.peak_spacing = None
    results = sim.run_dqd_search_fixed_barriers()
    assert results == []

def test_full_tuning_workflow():
    sim = StanzaDQDSimulator("TEST-04")
    # Mocking success to test the logic flow
    sim.device_health_check = lambda: True
    sim.compute_peak_spacing = lambda: 50.0

    report = sim.run_full_tuning()
    assert report["device"] == "TEST-04"
    assert report["dqd_count"] >= 0
    if report["dqd_count"] > 0:
        assert report["status"] == "SUCCESS"
        assert report["best_lambda2"] >= 0.85
    else:
        assert report["status"] == "FAILED"
