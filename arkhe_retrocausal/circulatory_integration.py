# Substrato 214: Circulatory System Integration

from arkhe_retrocausal.retrocausal_dream import RetrocausalDreamEngine, WakingInsight
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CirculatoryDecisionEngine:
    """
    Integrates Retrocausal Dream insights into financial/strategic decisions.
    """
    def __init__(self, agent_id: str = "circulatory_agent"):
        self.agent_id = agent_id
        self.applied_insights: List[WakingInsight] = []

    def influence_decision(self, current_decision_context: Dict[str, Any], insights: List[WakingInsight]) -> Dict[str, Any]:
        """
        Takes active WakingInsights and modifies the decision context.
        """
        logger.info(f"Integrando {len(insights)} insights retrocausais ao Sistema Circulatório.")

        modified_context = current_decision_context.copy()

        for insight in insights:
            if insight.confidence > 0.7:
                logger.info(f"Insight de alta confiança aplicado: {insight.description}")
                modified_context["retrocausal_bias"] = modified_context.get("retrocausal_bias", 0) + insight.phi_c_impact
                modified_context["suggested_actions"] = modified_context.get("suggested_actions", [])
                if insight.suggested_action:
                    modified_context["suggested_actions"].append(insight.suggested_action)
                self.applied_insights.append(insight)

        return modified_context
