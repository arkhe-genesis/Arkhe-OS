import pytest
from src.cathedral.energy.vacuum_interaction_framework import VacuumInteractionDriver

def test_p_occ_calculation():
    driver = VacuumInteractionDriver()
    assert driver.calculate_p_occ(10, 100) == 0.1
    assert driver.calculate_p_occ(0, 100) == 0.0
    assert driver.calculate_p_occ(10, 0) == 0.0

def test_n_b_calculation():
    driver = VacuumInteractionDriver()
    assert driver.calculate_n_b(0.5, 1.0) == 0.5
    assert driver.calculate_n_b(1.0, 1.0) == 1.0
    assert driver.calculate_n_b(1.0, 0) == 0.0

def test_phi_q_calculation():
    driver = VacuumInteractionDriver()
    assert driver.calculate_phi_q(2, 800) == 2.5e-3
    assert driver.calculate_phi_q(150, 800) == 0.1875
    assert driver.calculate_phi_q(150, 0) == float('inf')

def test_xi_calculation():
    driver = VacuumInteractionDriver()
    # Xi = (P_occ * N_b) / phi_q
    # (0.1 * 1.0) / 0.01 = 10.0
    assert driver.calculate_xi(0.1, 1.0, 0.01) == 10.0
    assert driver.calculate_xi(0.1, 1.0, 0) == float('inf')

def test_bare_trilayer_mapping():
    driver = VacuumInteractionDriver()
    results = driver.analyze_bare_trilayer(t_fe_nm=2.0, lambda_pump_nm=800.0, lambda_res_nm=800.0)

    assert results["p_occ"] == 2.5e-3
    assert results["n_b"] == 1.0
    assert results["phi_q"] == 2.5e-3
    # Xi = (2.5e-3 * 1.0) / 2.5e-3 = 1.0
    assert results["xi"] == 1.0

def test_nanoparticle_mapping():
    driver = VacuumInteractionDriver(kappa=1.0)
    coverage = 0.06
    g_local = 11.0 # Example local enhancement

    results = driver.analyze_with_nanoparticles(
        coverage=coverage,
        g_local=g_local,
        d_particle_nm=150.0,
        lambda_res_nm=800.0
    )

    # p_occ_eff = 0.06 * 11.0 = 0.66
    assert results["p_occ"] == pytest.approx(0.66)

    # n_b_eff = 1.0 + 0.06 * (11.0 - 1.0) = 1.0 + 0.6 = 1.6
    assert results["n_b"] == pytest.approx(1.6)

    # phi_q = 150 / 800 = 0.1875
    assert results["phi_q"] == 0.1875

    # xi = (0.66 * 1.6) / 0.1875 = 1.056 / 0.1875 = 5.632
    assert results["xi"] == pytest.approx(5.632)

    # enhancement = 1 + 1.0 * 0.06 * 5.632 = 1 + 0.33792 = 1.33792
    assert results["predicted_enhancement"] == pytest.approx(1.33792)

def test_enhancement_prediction():
    driver = VacuumInteractionDriver(kappa=2.0)
    xi = 5.0
    coverage = 0.1
    # 1 + 2.0 * 0.1 * 5.0 = 1 + 1.0 = 2.0
    assert driver.predict_enhancement(xi, coverage) == 2.0
