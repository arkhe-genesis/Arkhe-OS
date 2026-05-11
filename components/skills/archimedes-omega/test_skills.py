# test_skills.py
import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
import os

# Importar módulos a testar
from skills import (
    load_baseline,
    simulate_su2_continuous,
    simulate_sl3z_discrete,
    simulate_fibonacci_braid,
    simulate_w_state_coherence,
    detect_peaks,
    synthesize_conclusion,
    visualize_topology,
    evaluate_eqbe_safety,
    optimize_lipus_drug_interval,
    estimate_glymphatic_clearance,
    rainbow_coherence,
    simulate_rainbow_sl3z,
    simulate_rainbow_w_state
)


# ============================================================
# Testes: evaluate_eqbe_safety (Ético / EQBE)
# ============================================================
def test_evaluate_eqbe_safety_passed():
    """Verifica sucesso na auditoria quando critérios são atendidos."""
    theta = np.linspace(0, 1, 100)
    coherence = np.zeros(100) # Baixa interferência
    metadata = {"has_kill_switch": True, "timestamp": "2025-01-20"}

    # Mockando np.random.random para evitar falha aleatória no teste de leakage
    import unittest.mock as mock
    with mock.patch('numpy.random.random', return_value=0.5):
        report = evaluate_eqbe_safety("test_intervention", coherence, metadata)

    assert bool(report["is_safe"]) is True
    assert report["checks"]["leakage_test"] == "PASSED"
    assert report["checks"]["reversibility"] == "PASSED"


def test_evaluate_eqbe_safety_failed_no_kill_switch():
    """Verifica falha na auditoria quando não há kill switch."""
    theta = np.linspace(0, 1, 100)
    coherence = np.zeros(100)
    metadata = {"has_kill_switch": False}

    report = evaluate_eqbe_safety("unsafe_intervention", coherence, metadata)

    assert report["is_safe"] is False
    assert report["checks"]["reversibility"] == "FAILED"


# ============================================================
# Testes: simulate_w_state_coherence (Quântico/Coletivo)
# ============================================================
def test_simulate_w_state_coherence_output_shape(theta_range):
    """Verifica formato da saída."""
    phases, coherence = simulate_w_state_coherence(theta_range=theta_range)

    assert len(phases) == len(theta_range)
    assert len(coherence) == len(theta_range)


def test_simulate_w_state_coherence_values():
    """Verifica que coerência está no intervalo [0, 1]."""
    _, coherence = simulate_w_state_coherence()
    assert np.all(coherence >= 0.0)
    assert np.all(coherence <= 1.0)


def test_simulate_w_state_coherence_resilience():
    """Verifica que maior número de nodos aumenta a resiliência (piso de coerência)."""
    theta = np.linspace(0, 2*np.pi, 100)

    # Com 3 nodos
    _, coherence_3 = simulate_w_state_coherence(nodes=3, loss_probability=0.5, theta_range=theta)
    # Com 10 nodos
    _, coherence_10 = simulate_w_state_coherence(nodes=10, loss_probability=0.5, theta_range=theta)

    # O piso de coerência deve ser maior com 10 nodos (resiliência = 1 - 1/n)
    assert np.min(coherence_10) > np.min(coherence_3)


# ============================================================
# Fixtures
# ============================================================
@pytest.fixture
def theta_range():
    """Range padrão de fases para testes."""
    return np.linspace(0, 2*np.pi, 100)


@pytest.fixture
def temp_dir():
    """Diretório temporário para testes de I/O."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================
# Testes: load_baseline (Interpersonal)
# ============================================================
def test_load_baseline_with_file(temp_dir):
    """Testa carregamento com arquivo válido."""
    state_file = temp_dir / "tzinor-state.json"
    test_data = {
        "status": "ready",
        "coherence": 0.95,
        "temperature": 310.0,
        "sample_id": "BEXORG-3.0-001"
    }
    state_file.write_text(json.dumps(test_data))

    result = load_baseline(str(state_file))

    assert result["status"] == "ready"
    assert result["coherence"] == 0.95
    assert result["temperature"] == 310.0


def test_load_baseline_fallback():
    """Testa fallback quando arquivo não existe."""
    result = load_baseline("nonexistent-file-xyz.json")

    assert result["status"] == "cold_start"
    assert result["coherence"] == 0.0
    assert "temperature" in result


# ============================================================
# Testes: simulate_su2_continuous (Lógico/Naturalista)
# ============================================================
def test_simulate_su2_continuous_output_shape(theta_range):
    """Verifica formato da saída."""
    phases, coherence = simulate_su2_continuous(theta_range=theta_range)

    assert len(phases) == len(theta_range)
    assert len(coherence) == len(theta_range)
    assert phases.shape == coherence.shape


def test_simulate_su2_continuous_values():
    """Verifica que coerência está no intervalo válido."""
    theta = np.linspace(0, np.pi, 50)
    phases, coherence = simulate_su2_continuous(theta_range=theta)

    assert np.all(coherence >= -0.1), "Coerência não pode ser excessivamente negativa (considerando ruído)"
    assert np.all(coherence <= 1.1), "Coerência não pode exceder 1 significativamente (considerando ruído)"


def test_simulate_su2_continuous_decay():
    """Verifica comportamento de decaimento."""
    theta = np.linspace(0, 2*np.pi, 100)
    phases, coherence = simulate_su2_continuous(
        theta_range=theta,
        thermal_noise=0.1,
        temperature=310.0
    )

    # Coerência deve decair com o aumento do ângulo (efeito térmico)
    # Usando média das janelas iniciais/finais para ignorar ruído individual
    assert np.mean(coherence[:10]) > np.mean(coherence[-10:]), "Decaimento não observado"


def test_simulate_su2_continuous_temperature_effect():
    """Verifica efeito da temperatura na decoerência."""
    theta = np.linspace(0.1, np.pi, 50) # Evitar 0 para o fator térmico

    # Temperatura baixa = maior coerência
    _, coherence_low = simulate_su2_continuous(theta_range=theta, temperature=77)
    # Temperatura alta = menor coerência
    _, coherence_high = simulate_su2_continuous(theta_range=theta, temperature=400)

    assert np.mean(coherence_low) > np.mean(coherence_high), \
        "Temperatura alta deveria reduzir coerência"


# ============================================================
# Testes: simulate_fibonacci_braid (Topológico/Computacional)
# ============================================================
def test_simulate_fibonacci_braid_admissible():
    """Verifica comportamento dentro da região admissível."""
    result = simulate_fibonacci_braid(
        dalpha=0.0,
        epsilon=0.0,
        eta=0.0,
        lambda_=0.0
    )
    assert result["admissible"] is True
    assert result["braid_fidelity"] == 1.0
    assert result["leakage_probability"] == 0.0


def test_simulate_fibonacci_braid_outside_tolerance():
    """Verifica comportamento fora da região admissível."""
    result = simulate_fibonacci_braid(
        dalpha=0.1, # Muito acima do bound de ~0.004
        epsilon=0.0,
        eta=0.0,
        lambda_=0.0
    )
    assert result["admissible"] is False
    assert result["braid_fidelity"] < 1.0


# ============================================================
# Testes: simulate_sl3z_discrete (Espacial/Musical)
# ============================================================
def test_simulate_sl3z_discrete_output_shape(theta_range):
    """Verifica formato da saída."""
    phases, coherence = simulate_sl3z_discrete(theta_range=theta_range)

    assert len(phases) == len(theta_range)
    assert len(coherence) == len(theta_range)


def test_simulate_sl3z_discrete_resonance():
    """Verifica que há ressonância em π/5."""
    theta = np.linspace(0, 2*np.pi, 1000)
    phases, coherence = simulate_sl3z_discrete(theta_range=theta)

    # Encontrar índice mais próximo de π/5
    idx_pi5 = np.argmin(np.abs(phases - np.pi/5))

    # A coerência no pico deve ser significativa
    assert coherence[idx_pi5] > 0.1, \
        f"Pico em π/5 muito fraco: {coherence[idx_pi5]}"


def test_simulate_sl3z_discrete_words():
    """Verifica efeito de diferentes palavras do grupo."""
    theta = np.linspace(0, 2*np.pi, 500)

    # Com palavras diferentes
    _, coherence_with_words = simulate_sl3z_discrete(
        theta_range=theta,
        words=["a", "b", "ab", "ba"]
    )

    # Sem palavras (usará default)
    _, coherence_default = simulate_sl3z_discrete(theta_range=theta)

    # Devem ser diferentes
    assert not np.allclose(coherence_with_words, coherence_default), \
        "Palavras não afetam a coerência"


# ============================================================
# Testes: detect_peaks (Pragmático/Intrapessoal)
# ============================================================
def test_detect_peaks_single_peak():
    """Detecta um único pico bem definido."""
    theta = np.linspace(0, np.pi, 200)
    signal = np.zeros_like(theta)

    # Criar pico em π/5
    peak_idx = np.argmin(np.abs(theta - np.pi/5))
    signal[peak_idx] = 0.95
    # Adicionar um pouco de decaimento para não ser tudo zero
    signal += 0.01

    peaks = detect_peaks(signal, theta, threshold_multiplier=0.5, min_prominence=0.1)

    assert len(peaks) == 1
    assert abs(peaks[0]['phase'] - np.pi/5) < 0.05


def test_detect_peaks_no_peaks():
    """Retorna lista vazia quando não há picos."""
    theta = np.linspace(0, np.pi, 100)
    signal = np.ones(100) * 0.5 # Sinal constante

    peaks = detect_peaks(signal, theta, threshold_multiplier=2.0)

    assert len(peaks) == 0


# ============================================================
# Testes: synthesize_conclusion (Criativo/Existencial)
# ============================================================
def test_synthesize_conclusion_fibonacci_confirmed():
    """Testa confirmação de trança de Fibonacci."""
    peaks = [
        {'phase': np.pi/5, 'coherence': 0.98, 'is_resonance': True, 'fivefold_deviation_rad': 0.0},
        {'phase': 2*np.pi/5, 'coherence': 0.97, 'is_resonance': True, 'fivefold_deviation_rad': 0.0},
        {'phase': 4*np.pi/5, 'coherence': 0.96, 'is_resonance': True, 'fivefold_deviation_rad': 0.0}
    ]

    conclusion = synthesize_conclusion(peaks, threshold=0.95)

    assert conclusion['status'] == "FIBONACCI_BRAID_CONFIRMED"
    assert "Trança de Fibonacci" in conclusion['interpretation']


def test_synthesize_conclusion_discrete_confirmed():
    """Testa confirmação de reticulado discreto."""
    peaks = [
        {'phase': np.pi/5, 'coherence': 0.98, 'is_resonance': True, 'fivefold_deviation_rad': 0.0},
        {'phase': 2*np.pi/5, 'coherence': 0.96, 'is_resonance': True, 'fivefold_deviation_rad': 0.0}
    ]

    conclusion = synthesize_conclusion(peaks, threshold=0.95)

    assert conclusion['status'] == "DISCRETE_LATTICE_CONFIRMED"
    assert "ressonâncias" in conclusion['interpretation']


def test_synthesize_conclusion_no_signal():
    """Testa sem sinal detectado."""
    peaks = []

    conclusion = synthesize_conclusion(peaks, threshold=0.95)

    assert conclusion['status'] == "NO_SIGNAL"


# ============================================================
# Testes: visualize_topology (Visual/Practical)
# ============================================================
def test_visualize_topology_creates_file(temp_dir):
    """Verifica que arquivo de imagem é criado."""
    output_file = temp_dir / "test_coherence.png"

    su2_data = (
        np.linspace(0, 2*np.pi, 100),
        np.random.random(100)
    )
    sl3z_data = (
        np.linspace(0, 2*np.pi, 100),
        np.random.random(100)
    )
    peaks = []

    result = visualize_topology(
        su2_data, sl3z_data, peaks, str(output_file)
    )

    assert output_file.exists()
    assert result == str(output_file)


# ============================================================
# Testes: optimize_lipus_drug_interval
# ============================================================
def test_optimize_lipus_drug_interval():
    """Verifica se a otimização retorna valores coerentes."""
    result = optimize_lipus_drug_interval(
        t_peak=30.0,
        t_decay=60.0,
        drug_halflife=120.0,
        microbubbles=True,
        mi=0.4
    )

    assert "optimal_interval_min" in result
    assert "relative_absorption" in result
    assert result["optimal_interval_min"] > 0
    assert 0 <= result["relative_absorption"] <= 1.0


# ============================================================
# Testes: estimate_glymphatic_clearance
# ============================================================
def test_estimate_glymphatic_clearance():
    """Verifica estimativa de limpeza glinfática."""
    # Cenário de alta eficiência
    result_high = estimate_glymphatic_clearance(
        fret_coherence=0.9,
        phase_angle=0.0,
        lipus_intensity_mw_cm2=200.0,
        elapsed_minutes=60.0,
        baseline_coherence=0.3
    )
    assert result_high["response_category"] == "OTIMA"
    assert result_high["glymphatic_clearance_efficiency"] > 0.5

    # Cenário de baixa eficiência
    result_low = estimate_glymphatic_clearance(
        fret_coherence=0.35,
        phase_angle=0.0,
        lipus_intensity_mw_cm2=50.0,
        elapsed_minutes=5.0,
        baseline_coherence=0.3
    )
    assert result_low["response_category"] == "BAIXA"
    assert result_low["glymphatic_clearance_efficiency"] < 0.3


# ============================================================
# Testes: Rainbow Coherence
# ============================================================
def test_rainbow_coherence():
    """Verifica que a função rainbow_coherence produz picos centrados em pi/5."""
    # Se energy_ev = 0, rainbow_factor = 1.0, pico deve estar em pi/5
    val = rainbow_coherence(1.0, np.pi/5, 0.0)
    assert val == 1.0

    # Se energy_ev > 0, o ângulo físico que produz o pico deve mudar
    # f(E) = 1 / (1 - E/0.041). Se E = 0.0205, f(E) = 2.0.
    # effective_cartan = cartan_angle * 2.0.
    # Para ser pi/5, cartan_angle deve ser pi/10.
    val_shifted = rainbow_coherence(1.0, np.pi/10, 0.0205)
    assert abs(val_shifted - 1.0) < 1e-3

def test_detect_peaks_rainbow():
    """Verifica se detect_peaks reconhece ressonâncias deslocadas."""
    theta = np.linspace(0, 2*np.pi, 1000)

    # Simula SL3Z com energy_ev = 0.0205 (rainbow_factor = 2.0)
    # Pico nominal em pi/5 aparecerá em pi/10
    energy = 0.0205
    _, coherence = simulate_rainbow_sl3z(theta, energy_ev=energy, words=["a"])

    # Detectar picos sem informar a energia (deve falhar em reconhecer ressonância em pi/10)
    peaks_no_energy = detect_peaks(coherence, theta, threshold_multiplier=0.5)
    assert len(peaks_no_energy) > 0
    assert bool(peaks_no_energy[0]['is_resonance']) is False

    # Detectar picos informando a energia (deve reconhecer ressonância)
    peaks_with_energy = detect_peaks(coherence, theta, threshold_multiplier=0.5, energy_ev=energy)
    assert len(peaks_with_energy) > 0
    assert peaks_with_energy[0]['is_resonance'] is True
    assert peaks_with_energy[0]['rainbow_shift'] == 2.0


# ============================================================
# Executar testes
# ============================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
