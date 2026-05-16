import pytest
import asyncio
import numpy as np
import pandas as pd
from unittest.mock import AsyncMock, MagicMock

from federated.production_federated_detector import ProductionFederatedAggregator, ProductionFederatedReport
from compliance.regulatory_submission_engine import RegulatorySubmissionEngine, RegulatoryAgency
from healing.expanded_healing_actions import ExpandedHealingOrchestrator, ExpandedHealingAction
from ml.zero_day_production_trainer import ZeroDayProductionTrainer

class MockPhiBus:
    async def publish_metric(self, name, data):
        pass

class MockTemporalChain:
    async def anchor_event(self, name, data):
        return "mock_seal_123"

class MockHSM:
    async def sign(self, data):
        return "mock_signature"

@pytest.fixture
def mocks():
    return MockPhiBus(), MockTemporalChain(), MockHSM()

@pytest.mark.asyncio
async def test_federated_detector(mocks):
    phi, temp, hsm = mocks
    agg = ProductionFederatedAggregator("Org1", phi_bus=phi, temporal_chain=temp)

    # Valid report
    rep = ProductionFederatedReport(
        org_id="Org2", org_name="Bank2", timestamp=1000,
        anomaly_metrics={"anomaly_count": 2, "phi_c_impact": 0.1, "feature_count": 5},
        risk_distribution={"low": 1}, feature_distributions={"cpu_percent": {"mean": 0.8}},
        dp_noise_epsilon=3.0
    )
    res = await agg.submit_production_report(rep)
    assert res["status"] == "accepted"

    # Invalid epsilon
    rep_inv = ProductionFederatedReport(
        org_id="Org3", org_name="Bank3", timestamp=1000,
        anomaly_metrics={"anomaly_count": 2, "phi_c_impact": 0.1, "feature_count": 5},
        risk_distribution={"low": 1}, feature_distributions={},
        dp_noise_epsilon=1.0 # below 2.0
    )
    res_inv = await agg.submit_production_report(rep_inv)
    assert res_inv["status"] == "rejected"

@pytest.mark.asyncio
async def test_regulatory_engine(mocks):
    phi, temp, hsm = mocks
    engine = RegulatorySubmissionEngine("inst1", hsm_signer=hsm, temporal_chain=temp)

    sub = await engine.submit_report(
        RegulatoryAgency.ANATEL, "integrity", {"data": "test"}, "2024-01-01", "2024-01-31"
    )
    assert sub.agency == RegulatoryAgency.ANATEL
    assert sub.submission_status == "queued"

    # Test worker
    task = asyncio.create_task(engine._process_submission_queue())
    await asyncio.sleep(0.5)  # increased sleep time for task to finish

    hist = engine.get_submission_history()
    assert len(hist) == 1
    assert hist[0]["status"] in ["accepted", "rejected", "queued"]

    task.cancel()

@pytest.mark.asyncio
async def test_expanded_healing(mocks):
    phi, temp, hsm = mocks
    healer = ExpandedHealingOrchestrator(phi_bus=phi, temporal_chain=temp)

    # Test mapping
    anom = {"executable_path": "test.exe", "network_bytes": 10000}
    res = await healer.execute_healing(anom)
    assert res["success"] is True
    assert res["feature"] == "network_bytes"

    stats = healer.get_action_statistics()
    assert stats["total_healings"] == 1

    cat = healer.get_expanded_action_catalog()
    assert "network_bytes" in cat
    assert len(cat["network_bytes"]) == 3

@pytest.mark.asyncio
async def test_zero_day_trainer(mocks):
    phi, temp, hsm = mocks
    trainer = ZeroDayProductionTrainer(temporal_chain=temp, phi_bus=phi)

    df = await trainer.collect_training_data(days_back=1, include_threat_intel=False)
    assert not df.empty

    # Needs at least some valid data to train without error
    if len(df) > 10:
        res = await trainer.train_model(df, "test_model")
        assert res.model_type == "IsolationForest+RandomForest_ensemble"

        test_feat = {f: 0.5 for f in trainer.BEHAVIORAL_FEATURES}
        pred = await trainer.predict_zero_day(test_feat)
        assert "is_zero_day" in pred
        assert "recommendation" in pred
