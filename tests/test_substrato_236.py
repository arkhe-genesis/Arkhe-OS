import pytest
import os
import json
import asyncio
from opencode.opencode_canon import OpenCodeConfig, OpenCodeCanonicalTool

class MockTemporalChain:
    """Mock for TemporalChain anchoring."""
    async def anchor_event(self, event_type: str, data: dict):
        return f"mock_seal_{event_type}_{hash(str(data))}"

@pytest.fixture
def temp_config_file(tmp_path):
    return str(tmp_path / "test_opencode.json")

@pytest.fixture
def opencode_tool():
    config = OpenCodeConfig(
        config_path="dummy.json",
        model="claude-sonnet-4-20250514",
        provider="anthropic",
        phi_c_threshold=0.85
    )
    temporal = MockTemporalChain()
    return OpenCodeCanonicalTool(config, temporal=temporal)

@pytest.mark.asyncio
async def test_generate_config(opencode_tool, temp_config_file):
    params = {"output_path": temp_config_file}
    result = opencode_tool.generate_config(params)

    assert os.path.exists(temp_config_file)
    assert result["assistant"]["provider"]["model"] == "claude-sonnet-4-20250514"
    assert result["arkhe_metadata"]["phi_c_threshold"] == 0.85

@pytest.mark.asyncio
async def test_validate_config(opencode_tool, temp_config_file):
    # First generate it
    opencode_tool.generate_config({"output_path": temp_config_file})

    # Then validate it
    result = await opencode_tool.validate_config({"config_path": temp_config_file})

    assert result["all_passed"] is True
    assert result["phi_c"] == 0.95
    assert result["recommendation"] == "approve"

@pytest.mark.asyncio
async def test_execute_opencode_error(opencode_tool):
    result = await opencode_tool.execute_opencode({"prompt": "test prompt", "working_dir": "."})

    # Since opencode is not installed, it will raise FileNotFoundError which should be caught and returned as an error state
    assert result["status"] == "error"
    assert result["reason"] == "opencode executable not found"


@pytest.mark.asyncio
async def test_execute_opencode_no_prompt(opencode_tool):
    result = await opencode_tool.execute_opencode({"working_dir": "."})

    # Since opencode is not installed, it will raise FileNotFoundError which should be caught and returned as an error state
    # This specifically checks that we don't get an AttributeError on empty prompt
    assert result["status"] == "error"
    assert result["reason"] == "opencode executable not found"
