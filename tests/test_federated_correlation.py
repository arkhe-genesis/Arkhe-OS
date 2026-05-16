import pytest
import asyncio
import time
import numpy as np

from federated.production_federated_detector import ProductionFederatedAggregator, ProductionFederatedReport

@pytest.fixture
def mock_temporal_chain():
    class MockTemporal:
        async def anchor_event(self, event_type, data):
            return "mock_seal_123"
    return MockTemporal()

@pytest.fixture
def mock_phi_bus():
    class MockPhiBus:
        async def publish_metric(self, name, data):
            pass
    return MockPhiBus()

def test_add_laplace_noise():
    """Validação de DP: verificar que ε calibrado produz ruído esperado."""
    aggregator = ProductionFederatedAggregator(org_id="OrgTest")

    # Com ε menor, a variância do ruído deve ser maior (mais privacidade)
    noise_high_privacy = [aggregator._add_laplace_noise(0, epsilon=2.0) for _ in range(1000)]
    var_high = np.var(noise_high_privacy)

    # Com ε maior, a variância do ruído deve ser menor (menos privacidade)
    noise_low_privacy = [aggregator._add_laplace_noise(0, epsilon=5.0) for _ in range(1000)]
    var_low = np.var(noise_low_privacy)

    assert var_high > var_low

    # Deve rejeitar ε inválido
    with pytest.raises(ValueError):
        aggregator._add_laplace_noise(10, epsilon=0.0)

@pytest.mark.asyncio
async def test_cross_org_correlation(mock_temporal_chain, mock_phi_bus):
    """Teste de integração para correlação cross-org com 3+ parceiros."""
    aggregator = ProductionFederatedAggregator(
        org_id="BancoCentral",
        temporal_chain=mock_temporal_chain,
        phi_bus=mock_phi_bus
    )

    base_time = time.time()

    # Simula 3 organizações reportando anomalias muito similares no mesmo período
    report1 = ProductionFederatedReport(
        org_id="BancoDoBrasil", org_name="BB", timestamp=base_time,
        anomaly_metrics={"anomaly_count": 50, "phi_c_impact": 0.2, "feature_count": 5},
        risk_distribution={"low": 10, "high": 40},
        feature_distributions={
            "failed_login_rate": {"mean": 10.5},
            "unusual_time_access": {"mean": 8.0}
        },
        dp_noise_epsilon=3.0,
        pqc_signature="valid_sig_bb"
    )

    report2 = ProductionFederatedReport(
        org_id="Itau", org_name="Itaú", timestamp=base_time + 10,
        anomaly_metrics={"anomaly_count": 45, "phi_c_impact": 0.18, "feature_count": 5},
        risk_distribution={"low": 5, "high": 40},
        feature_distributions={
            "failed_login_rate": {"mean": 10.4},
            "unusual_time_access": {"mean": 8.1}
        },
        dp_noise_epsilon=3.0,
        pqc_signature="valid_sig_itau"
    )

    report3 = ProductionFederatedReport(
        org_id="Bradesco", org_name="Bradesco", timestamp=base_time + 20,
        anomaly_metrics={"anomaly_count": 60, "phi_c_impact": 0.22, "feature_count": 5},
        risk_distribution={"low": 15, "high": 45},
        feature_distributions={
            "failed_login_rate": {"mean": 10.6},
            "unusual_time_access": {"mean": 7.9}
        },
        dp_noise_epsilon=3.0,
        pqc_signature="valid_sig_bradesco"
    )

    # Submete os 3 reports
    res1 = await aggregator.submit_production_report(report1)
    res2 = await aggregator.submit_production_report(report2)
    res3 = await aggregator.submit_production_report(report3)

    assert res1["status"] == "accepted"
    assert res2["status"] == "accepted"
    assert res3["status"] == "accepted"

    # A terceira submissão deve engatilhar a correlação (>= 3 parceiros com >= 2 features)
    assert res3.get("cross_org_alert") is not None

    # Verifica estatísticas de produção
    stats = aggregator.get_production_statistics()
    assert stats["partner_orgs"] == 3
    assert stats["cross_org_alerts"] == 1

    # Verifica se os parceiros estão todos envolvidos no alerta gerado
    alert = stats["last_alert"]
    assert "BancoDoBrasil" in alert["orgs_involved"]
    assert "Itau" in alert["orgs_involved"]
    assert "Bradesco" in alert["orgs_involved"]

    assert "failed_login_rate" in alert["common_features"]
    assert "unusual_time_access" in alert["common_features"]
