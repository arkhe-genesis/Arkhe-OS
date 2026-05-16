import pytest
import asyncio
import time
from federated.production_federated_detector import ProductionFederatedAggregator, ProductionFederatedReport
from compliance.regulatory_submission_engine import RegulatorySubmissionEngine, RegulatoryAgency
from healing.expanded_healing_actions import ExpandedHealingOrchestrator, ExpandedHealingAction
from ml.zero_day_production_trainer import ZeroDayProductionTrainer, ThreatIntelligenceFeed

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

@pytest.mark.asyncio
async def test_federated_production_detector(mock_temporal_chain, mock_phi_bus):
    aggregator = ProductionFederatedAggregator(
        org_id="BancoDoBrasil",
        temporal_chain=mock_temporal_chain,
        phi_bus=mock_phi_bus
    )

    report1 = ProductionFederatedReport(
        org_id="Itau", org_name="Itaú", timestamp=time.time(),
        anomaly_metrics={"anomaly_count": 10, "phi_c_impact": 0.05, "feature_count": 20},
        risk_distribution={"low": 5, "high": 5},
        feature_distributions={"feature1": {"mean": 1.0}},
        dp_noise_epsilon=3.0,
    )

    result = await aggregator.submit_production_report(report1)
    assert result["status"] == "accepted"

    # Validação do Epsilon
    report_bad_epsilon = ProductionFederatedReport(
        org_id="Itau", org_name="Itaú", timestamp=time.time(),
        anomaly_metrics={"anomaly_count": 10, "phi_c_impact": 0.05, "feature_count": 20},
        risk_distribution={"low": 5, "high": 5},
        feature_distributions={"feature1": {"mean": 1.0}},
        dp_noise_epsilon=1.0,
    )

    result_bad = await aggregator.submit_production_report(report_bad_epsilon)
    assert result_bad["status"] == "rejected"

@pytest.mark.asyncio
async def test_regulatory_submission_engine(mock_temporal_chain):
    engine = RegulatorySubmissionEngine(
        institution_id="INST_001",
        temporal_chain=mock_temporal_chain
    )

    await engine.start_submission_worker()

    submission = await engine.submit_report(
        agency=RegulatoryAgency.ANATEL,
        report_type="integrity",
        report_content={"status": "all_good"},
        period_start="2023-01-01",
        period_end="2023-01-31"
    )

    assert submission.submission_id is not None
    assert submission.agency == RegulatoryAgency.ANATEL

    # Aguardar processamento da fila
    await asyncio.sleep(0.5)

    status = await engine.check_submission_status(submission.submission_id)
    assert status["status"] == "accepted"

@pytest.mark.asyncio
async def test_expanded_healing_actions():
    orchestrator = ExpandedHealingOrchestrator()

    catalog = orchestrator.get_expanded_action_catalog()
    assert len(catalog) > 0
    assert "handle_count" in catalog

    anomaly_alert = {"executable_path": "test.exe", "alert_id": "123"}

    success = await orchestrator.execute_healing(anomaly_alert, ExpandedHealingAction.SCALE_UP_RESOURCES)
    assert success is True

    stats = orchestrator.get_action_statistics()
    assert stats["total_healings"] == 1

@pytest.mark.asyncio
async def test_zero_day_trainer():
    feeds = [
        ThreatIntelligenceFeed("MISP", "ioc", time.time(), 1000, 10, 0.8)
    ]

    trainer = ZeroDayProductionTrainer(threat_feeds=feeds)

    # Coletar dados de treinamento
    df = await trainer.collect_training_data(days_back=1)
    assert not df.empty

    # Treinar modelo
    result = await trainer.train_model(df)

    assert result.f1_score >= 0.0
    assert result.auc_roc >= 0.0

    # Prever anomalia
    sample_features = {f: 0.5 for f in trainer.BEHAVIORAL_FEATURES}
    pred = await trainer.predict_zero_day(sample_features)

    assert "is_zero_day" in pred
    assert "confidence_score" in pred
