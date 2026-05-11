import pytest
import os
import sys
from src.lib.state_anchor_parser import StateAnchorParser
from src.arkhe_economy.arc20.token import LambdaBackedToken
from src.arkhe_economy.agents.rio_liquidity_agent import RioLiquidityAgent

def test_arc20_mechanics():
    token = LambdaBackedToken("Test", "TST")
    # High coherence
    token.update_coherence(0.99)
    allowance = token.calculate_mint_allowance()
    assert allowance >= 1000
    token.mint("agent_test", allowance)
    assert token.balances["agent_test"] == allowance

    # Slashing
    token.update_coherence(0.60)
    slashed = token.slash_if_incoherent("agent_test")
    assert slashed > 0
    assert token.balances["agent_test"] < allowance

def test_liquidity_agent_decision():
    agent = RioLiquidityAgent()
    agent.market_lambda = 0.98
    action, _ = agent.decide()
    assert action in ["ADD_LIQUIDITY", "HOLD"]

    agent.market_lambda = 0.80
    action, _ = agent.decide()
    assert action == "WITHDRAW_LIQUIDITY"

def test_soul_parser():
    # Setup mock SOUL.md
    soul_content = "# SOUL.md - Agent-X\n\n## Miss\u00e3o\nProtect Phase\n\n## Coer\u00eancia M\u00ednima\n0.92"
    with open("TEST_SOUL.md", "w") as f:
        f.write(soul_content)

    parser = StateAnchorParser(soul_path="TEST_SOUL.md")
    soul = parser.parse_agent_soul("Agent-X")

    assert soul["mission"] == "Protect Phase"
    assert soul["min_lambda"] == 0.92

    os.remove("TEST_SOUL.md")

if __name__ == "__main__":
    pytest.main([__file__])
