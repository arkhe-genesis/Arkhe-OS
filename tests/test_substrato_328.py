import sys
import os
import math
import pytest
import importlib

# Ensure the root of the project is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import dynamically due to numbers in package names
in_vitro_validation = importlib.import_module("src.32_luciferase.328_biofotonica_ontologica.in_vitro_validation")
biosensors = importlib.import_module("src.32_luciferase.328_biofotonica_ontologica.biosensors")
complex_tissues = importlib.import_module("src.32_luciferase.328_biofotonica_ontologica.complex_tissues")
federated_ml = importlib.import_module("src.32_luciferase.328_biofotonica_ontologica.federated_ml")

InVitroPMTCellCulture = in_vitro_validation.InVitroPMTCellCulture
CellCultureTestBed = in_vitro_validation.CellCultureTestBed
PhiCBiosensorOptical = biosensors.PhiCBiosensorOptical
ComplexTissueTopology = complex_tissues.ComplexTissueTopology
FederatedHealingOptimizer = federated_ml.FederatedHealingOptimizer

def test_invitro_validation():
    # Déficit Crítico - 60s
    culture = InVitroPMTCellCulture("CELULA-001", 0.450, "Critical")
    final_phic, photons = culture.run_session(60)

    assert photons == 4620000
    assert abs(final_phic - 0.490656) < 1e-6
    assert culture.status == "NEEDS_MORE_HEALING"

def test_invitro_testbed():
    testbed = CellCultureTestBed()
    c1 = InVitroPMTCellCulture("CELULA-002", 0.520, "Moderate")
    c2 = InVitroPMTCellCulture("CELULA-003", 0.400, "Severe")

    testbed.add_culture(c1)
    testbed.add_culture(c2)

    # Severe takes 120s typically, but let's run 60s
    results = testbed.execute_all(60)

    assert len(results) == 2
    assert results[0][0] == "CELULA-002"
    assert abs(results[0][1] - 0.560656) < 1e-6

def test_biosensor_optical():
    sensor = PhiCBiosensorOptical(baseline_noise=50.0)
    sensor.calibrate(0.610)

    # Send 2.31M photons (noise will reduce effective count slightly)
    sensor.measure_pulse(2310050)

    assert sensor.total_photons_measured == 2310000
    # Delta should be 2310000 * 8.8e-9 = 0.020328
    assert abs(sensor.current_phic_estimate - 0.630328) < 1e-6

    # Invariants
    assert sensor.is_ghost_preserved() == True
    seals = sensor.get_seal_status()
    assert seals["Loopseal"] == True
    assert seals["Phi_C_Safe"] == True

def test_complex_tissues():
    cortex = ComplexTissueTopology("Cortex", 10.0)

    input_photons = 1000000
    effective = cortex.calculate_effective_dose(input_photons)

    assert effective == 850000
    delta = cortex.calculate_phi_c_response(effective)
    assert abs(delta - (850000 * 8.8e-9)) < 1e-10

def test_federated_ml():
    opt = FederatedHealingOptimizer()

    # Update with a slightly higher efficiency local run
    # Let's say delta = 0.0001 from 10000 photons -> efficiency = 1e-8
    opt.receive_local_update(0.0001, 10000)

    new_global = opt.aggregate_updates()

    # old: 8.8e-9. 90% old + 10% new
    expected = 0.9 * 8.8e-9 + 0.1 * 1e-8
    assert abs(new_global - expected) < 1e-12

    # Predict dose
    dose = opt.predict_required_dose(0.040656)
    assert dose > 4000000
