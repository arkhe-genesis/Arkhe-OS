import pytest
from arkhe_quantum_production.colmeia_amc import AbelianMultiCycleCode, ColmeiaVerificacoes

def test_amc_pseudo_threshold():
    amc = AbelianMultiCycleCode(144, 12, 10)
    assert amc.pseudo_threshold > 0.011

def test_amc_single_shot_correction():
    amc = AbelianMultiCycleCode(144, 12, 10)
    syndrome = [1, 0, 1]
    success, msg = amc.single_shot_correction(syndrome)
    assert success is True
    assert "single-shot" in msg.lower()

def test_colmeia_monitoring():
    colmeia = ColmeiaVerificacoes()
    success = colmeia.monitor_qubits([0, 1])
    assert success is True

def test_sliding_window():
    amc = AbelianMultiCycleCode(144, 12, 10)
    history = [[0,1], [1,0], [1,1], [0,0]]
    assert amc.sliding_window_decode(history) is True
