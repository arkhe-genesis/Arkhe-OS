
import asyncio
import pytest
from src.arkhe_core.iota_council import IOTACouncil

@pytest.mark.asyncio
async def test_iota_council_deliberation():
    council = IOTACouncil()
    intent = "Test intent for code generation"
    result = await council.deliberate(intent)

    assert result["intent"] == intent
    assert len(result["perspectives"]) == 4
    assert result["status"] == "COHERENT"
    assert "consensus" in result
    assert result["consensus"]["decision"] == "PROCEED_TO_SYNTHESIS"

if __name__ == "__main__":
    asyncio.run(test_iota_council_deliberation())
    print("Test Passed")
