import pytest
import numpy as np
from src.physics.sasc_em_engine import SASCEMEngine, EMSpecification

def test_heaviside0_prediction():
    engine = SASCEMEngine()
    geometry = np.random.rand(64, 64)
    freq = 900e6

    result = engine.heaviside0.predict(geometry, freq)

    assert "s_parameters" in result
    assert "lambda2" in result
    assert "jitter_ps" in result
    assert "passivity_check" in result
    assert result["lambda2"] > 0
    assert result["jitter_ps"] > 0
    assert result["s_parameters"].shape == (2, 2)

def test_marconi0_generation():
    engine = SASCEMEngine()
    spec = EMSpecification(
        frequency_range=(890e6, 910e6),
        target_lambda2=0.99,
        max_jitter_ps=2.1
    )

    optimization = engine.marconi0.generate_design(spec)

    assert optimization["convergence_status"] == "converged"
    assert "optimized_geometry" in optimization
    assert "predicted_performance" in optimization
    assert optimization["predicted_performance"]["lambda2"] >= 0.9

def test_sasc_em_engine_status():
    engine = SASCEMEngine()
    status = engine.status()

    assert status["engine"] == "SASC-EM"
    assert status["heaviside0_active"] is True
    assert status["marconi0_active"] is True
