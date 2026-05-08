import sys
import os
import time
import math
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from agi.system32.reputation.substrate_344_phi_rep_oracle import PhiRepOracle, ReputationComponents

def test_initial_score():
    oracle = PhiRepOracle()
    score = oracle.compute_score("agent_1")
    assert score == 0.0, "Score should be 0.0 for unknown agent"

def test_component_creation_and_touch():
    oracle = PhiRepOracle()
    components = oracle._get_or_create_components("agent_1")

    # Check default values
    assert components.karma == 0.5
    assert components.phi_c == 0.5
    assert components.casi_success_rate == 0.5
    assert components.uptime == 0.5

    last_update, _ = oracle.agent_reputations["agent_1"]
    time.sleep(0.01)
    oracle._touch("agent_1")
    new_update, _ = oracle.agent_reputations["agent_1"]

    assert new_update > last_update, "Touch should update the timestamp"

def test_exponential_decay():
    oracle = PhiRepOracle(half_life_days=1)

    # Initialize components
    oracle._get_or_create_components("agent_1")

    # Mock the internal time
    last_ts, comp = oracle.agent_reputations["agent_1"]

    # Test score at time of update
    score_now = oracle.compute_score("agent_1")

    # Move the update time back by 1 half-life (1 day = 86400 seconds)
    oracle.agent_reputations["agent_1"] = (last_ts - 86400, comp)

    score_later = oracle.compute_score("agent_1")

    # Score should be half
    assert round(score_later, 2) == round(score_now / 2, 2), "Score should be half after 1 half-life"

def test_update_signals():
    oracle = PhiRepOracle()

    # Mock _fetch_moltbook_karma to return fixed value
    def mock_fetch(agent_id):
        return 0.9
    oracle._fetch_moltbook_karma = mock_fetch

    oracle.update_moltbook_karma("agent_1")
    comp = oracle._get_or_create_components("agent_1")
    assert round(comp.karma, 2) == 0.9

    # Initial phi_c is 0.5. update with 1.0 (alpha 0.2) => 0.2*1.0 + 0.8*0.5 = 0.6
    oracle.update_phi_c("agent_1", 1.0)
    assert round(comp.phi_c, 2) == 0.6

    # Initial casi is 0.5. update with True (1.0, alpha 0.1) => 0.1*1.0 + 0.9*0.5 = 0.55
    oracle.update_casi_success("agent_1", True)
    assert round(comp.casi_success_rate, 2) == 0.55

    # Initial uptime is 0.5. update with False (0.0, alpha 0.05) => 0.05*0.0 + 0.95*0.5 = 0.475
    oracle.update_uptime("agent_1", False)
    assert round(comp.uptime, 3) == 0.475

def test_get_full_report_and_oracle_query():
    oracle = PhiRepOracle()
    oracle._get_or_create_components("agent_1")

    report = oracle.get_full_report("agent_1")
    assert report["agent_id"] == "agent_1"
    assert "phi_rep" in report
    assert "components" in report
    assert report["components"]["karma"] == 0.5

    query_result = oracle.handle_oracle_query("agent_1")
    assert query_result["agent_id"] == report["agent_id"]
    assert round(query_result["phi_rep"], 5) == round(report["phi_rep"], 5)
    assert query_result["components"] == report["components"]
