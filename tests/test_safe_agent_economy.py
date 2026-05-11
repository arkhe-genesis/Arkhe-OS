import pytest
import os
from src.arkhe_economy.agents.rio_liquidity_agent import RioLiquidityAgent
from src.cuda.continuous_reconciler import ContinuousReconciler
from src.lib.state_anchor_parser import StateAnchorParser

class MockGPUReconciler:
    def __init__(self):
        self.avg_lambda = 0.99
    def tick(self):
        return self

@pytest.fixture
def reconciler():
    gpu_rec = MockGPUReconciler()
    return ContinuousReconciler(gpu_reconciler=gpu_rec)

@pytest.fixture
def agent():
    return RioLiquidityAgent(agent_id="Rio-Liquidity-01", safe_address="0xMockSafeAddress")

def test_rio_liquidity_agent_twap(agent):
    """Verify TWAP slice execution logic for the Rio Liquidity Agent."""
    agent.market_lambda = 0.99 # Stable market
    action = agent.execute()

    assert action == "TWAP_EXECUTE"
    assert agent.position < 1000.0 # Tokens spent
    assert any(s["status"] == "EXECUTED" for s in agent.twap_schedule)

def test_rio_liquidity_agent_volatility(agent):
    """Verify agent withdraws liquidity during high volatility (\u03bb\u2082 < 0.85)."""
    agent.market_lambda = 0.70 # Highly volatile
    action = agent.execute()

    assert action == "WITHDRAW_LIQUIDITY"
    assert agent.position > 1000.0 # Re-balanced to tokens

def test_safe_configuration_in_env():
    """Verify that SAFE_OWNER_KEY is configured in the environment template."""
    with open(".env.example", "r") as f:
        content = f.read()
    assert "SAFE_OWNER_KEY=" in content
    assert "SAFE_ADDRESS=" in content

def test_continuous_reconciler_integration(reconciler):
    """Verify Reconciler correctly parses identity and ticks GPU logic."""
    # Ensure MEMORY.md exists for parser
    if not os.path.exists("MEMORY.md"):
        with open("MEMORY.md", "w") as f:
            f.write("Block: 847,826\nλ₂: 0.999\nHash: 0x...")

    stats = reconciler.tick()
    assert stats.avg_lambda == 0.99
    assert reconciler.shield.t_max == 700.0
