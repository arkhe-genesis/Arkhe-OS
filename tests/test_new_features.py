import pytest
from arkp_mobile.src.mobile_app import MobileAppSync, SyncStatus, MobileReviewTask
from arkp_plugin_sdk.src.plugin_sdk import EthicalPlugin, PluginTester
from arkp_orcid.src.orcid_integration import OrcidAPIClient, ReputationEnricher
import asyncio
from unittest.mock import AsyncMock

def test_mobile_app_sync():
    sync = MobileAppSync()
    task = MobileReviewTask(
        task_id="t1", package_name="pkg", risk_score=0.5, deadline=0.0, cached_data={}
    )
    sync.local_store["t1"] = task
    assert sync.save_local_vote("t1", "APPROVED", "Rationale") == True
    assert sync.local_store["t1"].local_vote == "APPROVED"
    assert sync.local_store["t1"].sync_status == SyncStatus.OFFLINE

def test_plugin_sdk():
    class TestPlugin(EthicalPlugin):
        @property
        def plugin_metadata(self):
            return {"id": "test"}
        def evaluate(self, package_data, context):
            return {"score": 1.0}

    plugin = TestPlugin()
    assert plugin.plugin_metadata == {"id": "test"}
    assert PluginTester.run_tests(plugin, [{"input": {}, "expected_score": 1.0}]) == True

@pytest.mark.asyncio
async def test_orcid_integration():
    mock_client = OrcidAPIClient()
    mock_client.get_works = AsyncMock(return_value=[{"title": {"title": {"value": "Paper"}}}])

    enricher = ReputationEnricher(mock_client)
    res = await enricher.enrich_reviewer_profile("0000-0000-0000-0000")
    assert res["publications_count"] == 1
    assert res["reputation_bonus"] == 0.01
