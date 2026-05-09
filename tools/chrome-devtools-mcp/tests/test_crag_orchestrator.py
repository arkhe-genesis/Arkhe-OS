import pytest
import asyncio
from unittest.mock import MagicMock
from arkhe_os.core.unified_orchestrator import UnifiedFieldOrchestrator

@pytest.mark.asyncio
async def test_crag_orchestrator_integration():
    mock_field = MagicMock()
    mock_ethics = MagicMock()

    orchestrator = UnifiedFieldOrchestrator(mock_field, mock_ethics)

    query = "Test query for C-RAG"
    context = "Source context"
    zone = "beta"

    # First query - should execute
    result1 = await orchestrator.process_c_rag_query(query, context, zone=zone)
    assert "safety" in result1
    assert "coherence_7d" in result1
    assert "merkle_proof" in result1

    # Second query - should hit cache
    result2 = await orchestrator.process_c_rag_query(query, context, zone=zone)
    assert result1 is result2

    # Test dashboard
    dashboard = orchestrator.get_dashboard()
    assert dashboard["odometro"] == "002154"
    assert "crag" in dashboard["phase"]
