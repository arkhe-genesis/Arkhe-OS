import pytest
import numpy as np

from arkhe_os.coherence.path_coherence_estimator import AdaptiveBaselineEstimator

def test_baseline_initialization():
    estimator = AdaptiveBaselineEstimator(alpha=0.1)

    # Initialization
    val = estimator.update_baseline("node_a", 50.0)
    assert val == 50.0
    assert estimator.baselines["node_a"] == 50.0

def test_ema_update():
    estimator = AdaptiveBaselineEstimator(alpha=0.1)

    # First measurement
    estimator.update_baseline("node_a", 50.0)

    # Second measurement (alpha = 0.1)
    # EMA = 0.1 * 60.0 + 0.9 * 50.0 = 6.0 + 45.0 = 51.0
    val = estimator.update_baseline("node_a", 60.0)
    assert np.isclose(val, 51.0)
    assert np.isclose(estimator.baselines["node_a"], 51.0)

    # Third measurement
    # EMA = 0.1 * 40.0 + 0.9 * 51.0 = 4.0 + 45.9 = 49.9
    val = estimator.update_baseline("node_a", 40.0)
    assert np.isclose(val, 49.9)

def test_coherence_computation():
    estimator = AdaptiveBaselineEstimator(alpha=0.1, r_max=1000.0)

    # Set baseline manually for predictable output
    estimator.baselines["node_a"] = 50.0

    # Perfect scenario (rtt_avg = baseline, 0 loss, 0 jitter)
    coherence = estimator.compute_coherence("node_a", rtt_avg=50.0, loss=0.0, jitter=0.0)
    # latency_factor = max(0, 1 - (50-50)/(1000-50)) = 1
    # reliability = 1 - 0 = 1
    # jitter = exp(0) = 1
    # coherence = 1
    assert np.isclose(coherence, 1.0)

    # Degraded RTT scenario
    # latency_factor = max(0, 1 - (200-50)/(1000-50)) = 1 - 150/950 ≈ 0.842
    coherence = estimator.compute_coherence("node_a", rtt_avg=200.0, loss=0.0, jitter=0.0)
    assert 0.8 < coherence < 0.9

    # Heavy packet loss scenario
    coherence = estimator.compute_coherence("node_a", rtt_avg=50.0, loss=0.5, jitter=0.0)
    # factor = 1 * 0.5 * 1 = 0.5
    assert np.isclose(coherence, 0.5)

    # High jitter scenario
    coherence = estimator.compute_coherence("node_a", rtt_avg=50.0, loss=0.0, jitter=10.0)
    # jitter_factor = exp(-1) = 0.367
    assert np.isclose(coherence, np.exp(-1.0))
