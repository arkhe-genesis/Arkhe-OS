import pytest
from arkhe_retrocausal.retrocausal_dream import WakingInsight
from arkhe_retrocausal.circulatory_integration import CirculatoryDecisionEngine

def test_circulatory_integration():
    engine = CirculatoryDecisionEngine()

    insights = [
        WakingInsight(
            insight_id="ins1",
            episode_id="ep1",
            description="Buy low",
            phi_c_impact=0.1,
            confidence=0.8,
            suggested_action="increase_allocation"
        ),
        WakingInsight(
            insight_id="ins2",
            episode_id="ep1",
            description="Ignore",
            phi_c_impact=0.0,
            confidence=0.5
        )
    ]

    context = {"base_allocation": 100}
    new_context = engine.influence_decision(context, insights)

    assert "retrocausal_bias" in new_context
    assert new_context["retrocausal_bias"] == 0.1
    assert "increase_allocation" in new_context["suggested_actions"]
    assert len(engine.applied_insights) == 1
