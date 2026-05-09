"""
Substrate 284: Meta-Therapeutic Learning
Allows the Intervention Planner to reflect on its own predictions, record outcomes,
and propose auto-optimizations via internal consensus.
"""

import math
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class InterventionRecord:
    intervention_id: str
    target_pair: str
    predicted_phi_delta: float
    actual_phi_delta: float
    context: Dict[str, float] = field(default_factory=dict)

class MetaTherapeuticLearner:
    """Meta-learner that adapts intervention efficacy based on real-world outcomes."""

    def __init__(self, learning_rate: float = 0.05):
        self.learning_rate = learning_rate
        self.history: List[InterventionRecord] = []
        self.efficacy_weights: Dict[str, float] = {} # intervention_id -> weight modifier (default 1.0)
        self.confidence_scores: Dict[str, float] = {} # intervention_id -> score 0-1

    def record_outcome(self, record: InterventionRecord):
        """Records an intervention outcome for meta-learning."""
        self.history.append(record)
        self._update_weights(record)

    def _update_weights(self, record: InterventionRecord):
        """Updates internal efficacy weights based on the prediction error."""
        error = record.actual_phi_delta - record.predicted_phi_delta

        # Current weight
        current_weight = self.efficacy_weights.get(record.intervention_id, 1.0)

        # Simple proportional update (e.g., if actual > predicted, we underestimated)
        # Using a dampening factor based on baseline prediction
        if record.predicted_phi_delta != 0:
            adjustment = (error / max(abs(record.predicted_phi_delta), 0.01)) * self.learning_rate
        else:
            adjustment = 0.0

        new_weight = max(0.1, current_weight + adjustment)
        self.efficacy_weights[record.intervention_id] = new_weight

        self._update_confidence(record.intervention_id)

    def _update_confidence(self, intervention_id: str):
        """Updates the confidence score for an intervention based on prediction consistency."""
        records = [r for r in self.history if r.intervention_id == intervention_id]
        if not records:
            return

        # Calculate variance of errors
        errors = [r.actual_phi_delta - r.predicted_phi_delta for r in records]
        mean_error = sum(errors) / len(errors)
        variance = sum((e - mean_error) ** 2 for e in errors) / len(errors)

        # High variance -> low confidence
        # Using exponential decay mapping: var=0 -> conf=1, var=large -> conf~0
        confidence = math.exp(-variance * 10)
        self.confidence_scores[intervention_id] = confidence

    def propose_auto_optimizations(self) -> List[Dict]:
        """Proposes internal consensus adjustments to intervention parameters."""
        proposals = []
        for intervention_id, weight in self.efficacy_weights.items():
            if abs(weight - 1.0) > 0.1: # Significant deviation
                confidence = self.confidence_scores.get(intervention_id, 0.0)
                if confidence > 0.6:
                    proposals.append({
                        "intervention_id": intervention_id,
                        "proposed_efficacy_multiplier": weight,
                        "confidence": confidence,
                        "reasoning": f"Consistent prediction error detected. Adjusting multiplier to {weight:.2f}."
                    })
        return proposals

    def get_adjusted_prediction(self, intervention_id: str, base_prediction: float) -> float:
        """Returns the base prediction adjusted by the meta-learned weights."""
        weight = self.efficacy_weights.get(intervention_id, 1.0)
        return base_prediction * weight
