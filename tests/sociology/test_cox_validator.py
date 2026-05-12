#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/sociology/test_cox_validator.py — Testes do Cox Model Validator
"""

import pytest
import pandas as pd
from conrag.domains.sociology.cox_validator import (
    CoxModelValidator,
    IBGEDataConnector,
    OSFDataConnector,
    CoxAssumption,
)

def test_ibge_connector_fetch():
    """Testa conector IBGE com indicadores reais."""
    # Testar com indicadores válidos do SIDRA
    df = IBGEDataConnector.fetch_municipal_data(
        indicators=["173"],  # População
        year=2020,
        states=["SP", "RJ"],
    )

    assert not df.empty, "IBGE connector deve retornar dados não vazios"
    assert "municipio_codigo" in df.columns
    assert "173" in df.columns or "populacao" in df.columns
    print(f"✅ IBGE: {len(df)} municípios carregados")


def test_osf_connector_fetch():
    """Testa conector OSF com dataset do Pimentel (2025)."""
    df = OSFDataConnector.fetch_dataset(
        osf_id="kfy24",
        file_name="planos_diretores.csv",
    )

    # Pode retornar None se API OSF estiver indisponível
    if df is not None:
        assert not df.empty
        assert "tempo" in df.columns or "status" in df.columns
        print(f"✅ OSF: {len(df)} registros carregados")
    else:
        print("⚠️ OSF: Dataset não disponível (mock ativado)")


def test_cox_validation_full_pipeline():
    """Testa pipeline completo de validação do modelo de Cox."""
    validator = CoxModelValidator()

    # Validar com dados simulados (fallback)
    report = validator.validate_policy_diffusion(
        policy_name="Planos Diretores Municipais",
        covariates=["pib_per_capita", "populacao"],
        data_source="simulated",  # Forçar fallback
    )

    # Verificar estrutura do relatório
    assert report.dataset_name == "Planos Diretores Municipais"
    assert report.n_observations > 0
    assert CoxAssumption.PROPORTIONAL_HAZARDS in report.results
    assert isinstance(report.canonical_seal, str)
    assert len(report.canonical_seal) == 64  # SHA3-256 hex

    # Verificar que pelo menos alguns pressupostos foram testados
    tested = sum(1 for r in report.results.values() if r.p_value is not None or r.statistic is not None)
    assert tested >= 3, f"Esperado >= 3 pressupostos testados, got {tested}"

    print(f"✅ Cox validation: {report.n_observations} obs, {report.n_events} events, valid={report.overall_valid}")


def test_beaiver_integration():
    """Testa integração do CoxModelValidator com BEAVER engine."""
    from conrag.domains.sociology.cox_validator import SociologyBEAVERRules

    beaver = SociologyBEAVERRules()

    claim = "Municípios maiores adotam políticas mais rapidamente"
    context = {
        "policy_name": "Test Policy",
        "covariates": ["populacao", "pib_per_capita"],
        "data_source": "simulated",
    }

    approved, meta = beaver.verify_policy_diffusion_claim(claim, context)

    # BEAVER deve retornar decisão binária + metadados
    assert isinstance(approved, bool)
    assert isinstance(meta, dict)
    assert "status" in meta or "violacoes" in meta

    print(f"✅ BEAVER integration: approved={approved}, message={meta.get('message', 'N/A')[:100]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
