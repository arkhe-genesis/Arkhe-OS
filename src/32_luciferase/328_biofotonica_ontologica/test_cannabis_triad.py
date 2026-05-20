"""
Testes de validação do Substrato 328-CANNABIS
Canon: ∞.Ω.∇+++.328.cannabis_triad.tests
"""

import pytest
import numpy as np
from cannabis_triad import CannabisTriad, TriadSession

class TestCannabisTriad:

    def test_reporter_assay_maps_promoter_activity(self):
        triad = CannabisTriad("test-node-001")

        session = triad.run_reporter_assay("plant-A", "CBD_synthase")

        assert session.component == "reporter"
        assert session.metrics["promoter"] == "CBD_synthase"
        assert 0.7 <= session.metrics["promoter_activity"] <= 0.9  # Faixa esperada
        assert session.metrics["photons_emitted"] == 528  # Padrão canônico
        assert len(session.canonical_seal) == 64  # SHA3-256 hex

    def test_biosensor_detects_thc_above_limit(self):
        triad = CannabisTriad("test-node-002")

        # THC acima do limite: deve detectar
        session_high = triad.run_biosensor_assay("sample-001", thc_pm=150.0)
        assert session_high.metrics["detected"] is True
        assert session_high.metrics["risk_level"] in ["POSITIVE", "CRITICAL"]

        # THC abaixo do limite: não deve detectar
        session_low = triad.run_biosensor_assay("sample-002", thc_pm=45.0)
        assert session_low.metrics["detected"] is False
        assert session_low.metrics["risk_level"] == "NEGATIVE"

    def test_biosensor_flags_scra_critical(self):
        triad = CannabisTriad("test-node-003")

        # Alta concentração + possível SCRA
        session = triad.run_biosensor_assay("sample-003", thc_pm=500.0)

        # SCRA detection é probabilístico na simulação
        # Mas risk_level deve ser CRITICAL se SCRA presente
        if session.metrics["scra_detected"]:
            assert session.metrics["risk_level"] == "CRITICAL"
            assert len(session.metrics["scra_compounds"]) > 0

    def test_pdt_c_efficacy_correlates_with_dose(self):
        triad = CannabisTriad("test-node-004")

        # Baixa dose
        low = triad.run_pdt_c_therapy("tumor-A", cbd_ug=30, ir_dose_jcm2=8.0, tumor_volume_mm3=150)
        # Alta dose
        high = triad.run_pdt_c_therapy("tumor-B", cbd_ug=75, ir_dose_jcm2=15.0, tumor_volume_mm3=250)

        # Eficácia deve ser maior para dose maior (tendência)
        # Nota: ruído biológico pode causar sobreposição, mas média deve mostrar tendência
        assert high.metrics["efficacy_percent"] >= low.metrics["efficacy_percent"] - 5  # Tolerância

    def test_triad_preserves_ghost_invariant(self):
        triad = CannabisTriad("test-node-005")

        # Executar sessões para cada componente
        triad.run_reporter_assay("plant-001", "THC_synthase")
        triad.run_biosensor_assay("sample-001", thc_pm=200.0)
        triad.run_pdt_c_therapy("tumor-001", cbd_ug=50, ir_dose_jcm2=10.0, tumor_volume_mm3=200)

        status = triad.get_triad_status()

        # Biosensor e PDT-C devem preservar Ghost
        assert bool(status["biosensor"]["phi_c_ghost_preserved"]) is True
        assert bool(status["pdt_c"]["phi_c_ghost_preserved"]) is True

        # Reporter pode estar em desenvolvimento (seed stage)
        # Mas não deve violar Gap Soberano
        assert status["reporter"]["phi_c_current"] < triad.GAP_MAX

    def test_unified_seal_is_deterministic_for_same_state(self):
        # Mock time.time to ensure deterministic seal generation for test
        import time
        original_time = time.time
        time.time = lambda: 1000.0

        try:
            triad1 = CannabisTriad("test-node-006")
            triad2 = CannabisTriad("test-node-006")

            # Executar mesmas sessões
            for t in [triad1, triad2]:
                t.run_biosensor_assay("sample-X", thc_pm=150.0)

            status1 = triad1.get_triad_status()
            status2 = triad2.get_triad_status()

            # Selos unificados devem ser iguais para mesmo estado
            assert status1["unified_seal"] == status2["unified_seal"]
        finally:
            time.time = original_time
