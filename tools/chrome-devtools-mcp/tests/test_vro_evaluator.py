import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from deploy.azure.vro_evaluator import evaluate_task, update_vector, cosine_similarity

@pytest.mark.asyncio
@patch("deploy.azure.vro_evaluator.get_reputation_vector", new_callable=AsyncMock)
@patch("deploy.azure.vro_evaluator.store_reputation_vector", new_callable=AsyncMock)
async def test_vro_evaluator_trigger(mock_store, mock_get):
    mock_get.return_value = {"semantic": 800, "originality": 700}

    mock_msg = MagicMock()
    mock_msg.message_id = "task-123"
    mock_msg.get_body.return_value = json.dumps({
        "intent_embedding": [0.1, 0.2, 0.3],
        "result_embedding": [0.11, 0.21, 0.31],
        "agent_did": "did:arkhe:agent1",
        "task_id": "task-123"
    }).encode()

    await evaluate_task(mock_msg)

    mock_get.assert_called_with("did:arkhe:agent1")
    mock_store.assert_called_once()
    args, _ = mock_store.call_args
    assert args[0] == "did:arkhe:agent1"
    assert "semantic" in args[1]

def test_cosine_similarity():
    a = [1, 0]
    b = [1, 0]
    assert cosine_similarity(a, b) == pytest.approx(1.0)

    c = [0, 1]
    assert cosine_similarity(a, c) == pytest.approx(0.0)

def test_update_vector():
    current = {"semantic": 800, "originality": 700}
    # Test high similarity
    new = update_vector(current, 0.9, 0.9)
    assert new['semantic'] == 810
    assert new['originality'] > 700

    # Test low similarity
    new_low = update_vector(current, 0.5, 0.8)
    assert new_low['semantic'] == 750
