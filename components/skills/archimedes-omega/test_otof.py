import pytest
from skills import simulate_auditory_coherence, simulate_brillouin_auditory_sensor

def test_simulate_auditory_coherence():
    # Teste de recuperação temporal
    baseline = 106.0
    res_4w = simulate_auditory_coherence(baseline, 4.0)
    res_12w = simulate_auditory_coherence(baseline, 12.0)

    assert res_4w["hearing_threshold_db"] < baseline
    assert res_12w["hearing_threshold_db"] < res_4w["hearing_threshold_db"]
    assert res_12w["lambda2_coherence"] > res_4w["lambda2_coherence"]
    assert res_12w["status"] == "STABILIZED"

def test_simulate_brillouin_auditory_sensor():
    # Teste de sensor com boa resposta
    res_good = simulate_brillouin_auditory_sensor(1000.0, 0.5)
    assert res_good["laser_wavelength_nm"] == 674.0

    # Teste de sensor com resposta fraca (incoerente)
    res_bad = simulate_brillouin_auditory_sensor(1000.0, 0.05)
    assert res_bad["is_coherent"] is False

if __name__ == "__main__":
    # Execução manual
    print("Executando Simulação OTOF (4 semanas)...")
    print(simulate_auditory_coherence(106.0, 4.0))
    print("\nExecutando Leitura Sensor Brillouin...")
    print(simulate_brillouin_auditory_sensor(1000.0, 0.4))
