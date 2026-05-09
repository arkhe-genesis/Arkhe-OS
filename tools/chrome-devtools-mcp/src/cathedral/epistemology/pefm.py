import numpy as np
from typing import Dict, List, Optional
from .enrichment import EnrichedFeatures

class PEFM:
    """
    PEFM (Predictive Epistemic Failure Model) v1.0
    A constraint-enforced model for anticipating epistemic failures.
    """

    def __init__(self):
        # I2: Monotonic Risk Response
        # We simulate the EBC behavior with deterministic monotonic functions for demonstration.
        # In production, this would be an ExplainableBoostingClassifier.
        self.weights = {
            "coherence_score": -0.5, # Lower coherence -> Higher failure risk
            "component_S": 0.2,      # Higher connectivity -> Higher potential for contamination
            "component_C": -0.8,     # Lower consistency -> Much higher failure risk
            "component_I": 0.3,
            "component_P": -0.2,
            "component_E": 1.5,      # High relevance -> Much higher criticality of failure
            "domain_sensitivity": 1.0
        }

    def predict_failure_probability(self, features: EnrichedFeatures) -> float:
        """
        Calculates p_fail based on enriched features.
        Enforces I1: Prediction != Ground Truth (it's a probability).
        """
        x = features.to_feature_vector()

        # Simplified linear combination with sigmoid for probability
        # Features: [score, S, C, I, P, E, vertex, edge, domain_sensitivity]
        # indices:   0      1  2  3  4  5  6       7     8

        logit = (
            self.weights["coherence_score"] * x[0] +
            self.weights["component_S"] * x[1] +
            self.weights["component_C"] * x[2] +
            self.weights["component_I"] * x[3] +
            self.weights["component_P"] * x[4] +
            self.weights["component_E"] * x[5] +
            self.weights["domain_sensitivity"] * x[8]
        )

        p_fail = 1.0 / (1.0 + np.exp(-logit))
        return float(p_fail)

    def explain(self, features: EnrichedFeatures) -> Dict[str, float]:
        """I4: Feature Transparency."""
        x = features.to_feature_vector()
        contributions = {
            "coherence": self.weights["coherence_score"] * x[0],
            "consistency": self.weights["component_C"] * x[2],
            "relevance": self.weights["component_E"] * x[5],
            "domain": self.weights["domain_sensitivity"] * x[8]
        }
        return contributions
