import asyncio
import os
import shutil
import tempfile
import pytest
import aiohttp
from unittest.mock import patch, MagicMock

from substrato_199_4_production_partner import ProductionPartnerOrchestrator, PartnerSector

@pytest.fixture
def temp_config_dir():
    # Create a temporary directory for testing
    dir_path = tempfile.mkdtemp()
    yield dir_path
    # Clean up after test
    shutil.rmtree(dir_path)

@pytest.mark.asyncio
async def test_register_partner(temp_config_dir):
    # Setup mock phi_bus and temporal
    mock_temporal = MagicMock()
    mock_temporal.anchor_event = MagicMock()

    # Needs a coroutine wrapper for async mock behavior
    async def mock_anchor_event(*args, **kwargs):
        return "mock_seal"
    mock_temporal.anchor_event.side_effect = mock_anchor_event

    orchestrator = ProductionPartnerOrchestrator(
        central_org_id="arkhe_central",
        temporal_chain=mock_temporal,
        config_path=temp_config_dir
    )

    partner_info = {
        "partner_id": "bank_x_123",
        "name": "Bank X",
        "sector": "banking",
        "epsilon": 3.5,
        "ticketing_system": "jira"
    }

    result = await orchestrator.register_partner(partner_info)
    assert result["status"] == "registered"
    assert result["partner_id"] == "bank_x_123"
    assert "pqc_public_key" in result

    # Check if partner is saved correctly
    assert "bank_x_123" in orchestrator._partners
    partner = orchestrator._partners["bank_x_123"]
    assert partner.name == "Bank X"
    assert partner.sector == PartnerSector.BANKING
    assert partner.privacy_budget["epsilon"] == 3.5

@pytest.mark.asyncio
async def test_receive_partner_anomalies(temp_config_dir):
    orchestrator = ProductionPartnerOrchestrator(
        central_org_id="arkhe_central",
        config_path=temp_config_dir
    )

    partner_info = {
        "partner_id": "bank_y_456",
        "name": "Bank Y",
        "sector": "banking"
    }

    await orchestrator.register_partner(partner_info)

    # Generate mock signature
    import json
    import hashlib
    payload = {"anomaly_count": 5, "cpu_percent": 85.0}
    expected_signature = hashlib.sha3_256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    anomaly_report = {
        "payload": payload,
        "pqc_signature": expected_signature
    }

    result = await orchestrator.receive_partner_anomalies("bank_y_456", anomaly_report)
    assert result["status"] == "accepted"

    # Validate it was saved
    assert len(orchestrator._partner_reports["bank_y_456"]) == 1

@pytest.mark.asyncio
async def test_cross_org_correlation(temp_config_dir):
    orchestrator = ProductionPartnerOrchestrator(
        central_org_id="arkhe_central",
        config_path=temp_config_dir
    )
    # Decrease min orgs to 2 to make testing easier without firing too many mock creations
    orchestrator.MIN_ORGS_FOR_ALERT = 2

    import json
    import hashlib

    # Register partners
    for pid in ["bank_1", "bank_2"]:
        await orchestrator.register_partner({"partner_id": pid, "name": pid})

    payload = {"anomaly_metrics": {"feat_A": 100, "feat_B": 50}}
    signature = hashlib.sha3_256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    # First report
    res1 = await orchestrator.receive_partner_anomalies("bank_1", {"payload": payload, "pqc_signature": signature})
    assert res1["status"] == "accepted"
    assert res1["alert_id"] is None

    # Second report with similar features should trigger correlation
    res2 = await orchestrator.receive_partner_anomalies("bank_2", {"payload": payload, "pqc_signature": signature})
    assert res2["status"] == "accepted"
    assert res2["alert_id"] is not None

    assert len(orchestrator._cross_org_alerts) == 1
    alert = orchestrator._cross_org_alerts[0]
    assert "bank_1" in alert["orgs_involved"]
    assert "bank_2" in alert["orgs_involved"]
