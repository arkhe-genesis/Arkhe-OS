import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Mock the modules before importing PitchAgent
import sys
mock_servicebus = MagicMock()
sys.modules["azure.servicebus.aio"] = mock_servicebus
sys.modules["azure.servicebus"] = MagicMock()
mock_cosmos = MagicMock()
sys.modules["azure.cosmos.aio"] = mock_cosmos
sys.modules["azure.cosmos"] = MagicMock()
sys.modules["langchain_openai"] = MagicMock()
sys.modules["langchain_core.prompts"] = MagicMock()

from arkhe_brain.pitch_agent import PitchAgent

@pytest.mark.asyncio
async def test_pitch_agent_process_message():
    with patch("arkhe_brain.pitch_agent.ChatOpenAI") as mock_chat, \
         patch("arkhe_brain.pitch_agent.CosmosClient") as mock_cosmos_class:

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock()
        mock_chat.return_value = mock_llm

        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_container = MagicMock()
        mock_cosmos_class.from_connection_string.return_value = mock_client
        mock_client.get_database_client.return_value = mock_db
        mock_db.get_container_client.return_value = mock_container
        mock_container.upsert_item = AsyncMock()

        # Setup LLM response
        mock_response = MagicMock()
        mock_response.content = '```json\n{"refined_content": "Refined!", "themes": ["AI"], "impact_score": 0.9, "outline": ["Step 1"]}\n```'
        mock_llm.ainvoke.return_value = mock_response

        agent = PitchAgent()

        mock_msg = MagicMock()
        mock_msg.get_body.return_value = bytes(json.dumps({"content": "Original pitch content"}), 'utf-8')
        mock_msg.message_id = "test-id"

        await agent.process_message(mock_msg)

        # Assertions
        mock_llm.ainvoke.assert_called_once()
        mock_container.upsert_item.assert_called_once()
        args, _ = mock_container.upsert_item.call_args
        assert args[0]['original_pitch'] == "Original pitch content"
        assert args[0]['refined_data']['refined_content'] == "Refined!"
