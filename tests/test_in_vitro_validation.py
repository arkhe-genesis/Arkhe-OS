# tests/test_in_vitro_validation.py
"""
Testes para Substrato 329: Validação Experimental In Vitro
Canon: ∞.Ω.∇+++.329.tests
"""

import pytest, numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from ArkheNode.Bio.in_vitro_validator import InVitroValidator, BiophotonMeasurement, PhiCBiosensorReading

class TestInVitroValidator:

    def test_pmt_calibration_returns_valid_efficiency(self):
        validator = InVitroValidator("exp-001", "HEK293")
        calibration = validator.calibrate_pmt()

        assert 0.90 <= calibration["efficiency"] <= 1.0
        assert calibration["dark_count_rate"] > 0
        assert len(calibration["calibration_seal"]) == 64  # SHA3-256 hex

    def test_biophoton_measurement_subtracts_background(self):
        validator = InVitroValidator("exp-002", "HeLa")

        # Medição com sinal baixo (próximo do ruído)
        measurement = validator.measure_biophotons("well-B2", duration_s=10.0)

        assert measurement.background_subtracted is True
        assert measurement.photon_count >= 0  # Não negativo após subtração
        assert measurement.canonical_seal is not None

    def test_phi_c_reading_has_valid_confidence_interval(self):
        validator = InVitroValidator("exp-003", "fibroblast")

        reading = validator.measure_phi_c("cell-042", method="FLIM")

        assert 0.0 <= reading.phi_c_estimate <= 1.0
        ci_low, ci_high = reading.confidence_interval
        assert 0.0 <= ci_low <= reading.phi_c_estimate <= ci_high <= 1.0
        assert reading.measurement_method in ["FRET", "FLIM", "interferometry"]

    def test_healing_experiment_preserves_invariants(self):
        validator = InVitroValidator("exp-004", "neuron")

        results = validator.run_healing_experiment(target_phi_c=0.50, duration_s=30.0)

        # Invariantes devem ser preservados
        assert results["efficacy"]["invariants_preserved"]["ghost"] is True
        assert results["efficacy"]["invariants_preserved"]["gap"] is True

        # Φ_C deve melhorar ou permanecer estável
        assert results["efficacy"]["phi_c_delta"] >= -0.01  # Tolerância de ruído

        # Selos canônicos devem estar presentes
        assert len(results["canonical_seal"]) == 64

    def test_temporal_anchoring_generates_unique_seals(self):
        validator = InVitroValidator("exp-005", "cardiomyocyte")

        # Múltiplas medições devem gerar selos únicos
        seals = []
        for i in range(5):
            reading = validator.measure_phi_c(f"cell-{i}", method="FRET")
            seals.append(reading.canonical_seal)

        # Todos os selos devem ser únicos
        assert len(set(seals)) == len(seals)
        assert all(len(s) == 64 for s in seals)

    def test_coherence_length_estimation_is_reasonable(self):
        validator = InVitroValidator("exp-006", "epithelial")

        # Baixa contagem: coerência indefinida
        low_count = validator._estimate_coherence_length(50, duration_s=10.0)
        assert low_count is None

        # Alta contagem: coerência positiva mas limitada
        high_count = validator._estimate_coherence_length(5000, duration_s=10.0)
        assert 0.0 < high_count <= 10.0  # Máximo 10 cm
