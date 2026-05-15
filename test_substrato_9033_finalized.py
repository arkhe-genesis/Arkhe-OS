import pytest
from substrato_9033_finalized import run_demo

@pytest.mark.asyncio
async def test_demo_runs_without_errors():
    await run_demo()
