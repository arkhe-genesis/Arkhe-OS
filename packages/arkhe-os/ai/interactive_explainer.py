import torch
import numpy as np
from typing import Dict, Optional, Tuple
from arkhe_os.ai.visual_attention_explainer import VisualAttentionExplainer, AttentionExplanation

class NaturalLanguageInteractiveExplainer:
    """
    Wraps the VisualAttentionExplainer to allow administrators to ask
    questions about the CNN's decision using natural language.
    """
    def __init__(self, visual_explainer: VisualAttentionExplainer):
        self.visual_explainer = visual_explainer

    def ask(self, question: str, image: torch.Tensor, predicted_class: Optional[str] = None) -> str:
        """
        Parses a natural language question and generates a textual explanation
        based on the visual attention (Grad-CAM++) generated for the image.
        """
        question_lower = question.lower()

        # Get the visual explanation
        explanation = self.visual_explainer.explain_classification(image, predicted_class)

        # Map questions to simple rule-based textual responses for simulation
        if "why" in question_lower or "por que" in question_lower:
            return self._explain_why(explanation)
        elif "where" in question_lower or "onde" in question_lower:
            return self._explain_where(explanation)
        elif "confidence" in question_lower or "confiança" in question_lower:
            return self._explain_confidence(explanation)
        else:
            return "I am the interactive explainer. Try asking 'why', 'where', or 'confidence' about the classification."

    def _explain_why(self, explanation: AttentionExplanation) -> str:
        num_regions = len(explanation.top_regions)
        focus = explanation.explanation_metadata.get('attention_focus', 0.0)
        cls_name = explanation.predicted_class
        return (f"The model classified the state as {cls_name} because it identified "
                f"{num_regions} key regions of interest with an attention focus of {focus:.2f}.")

    def _explain_where(self, explanation: AttentionExplanation) -> str:
        if not explanation.top_regions:
            return "The model did not find any specific highly concentrated regions of attention."

        top_region = explanation.top_regions[0]
        # In the simulated visual explainer, it returns {'importance': 0.8}
        # A real one would have a 'bbox' or 'centroid'
        if 'centroid' in top_region:
            cx, cy = top_region['centroid']
            return f"The most important region is centered around pixel coordinates ({cx}, {cy})."
        else:
            imp = top_region.get('importance', 0.0)
            return f"The attention is spread across regions, with the most important region having an importance score of {imp:.2f}."

    def _explain_confidence(self, explanation: AttentionExplanation) -> str:
        cls_name = explanation.predicted_class
        conf = explanation.confidence * 100
        entropy = explanation.explanation_metadata.get('heatmap_entropy', 0.0)
        return (f"The model is {conf:.1f}% confident that the state is {cls_name}. "
                f"The attention map entropy is {entropy:.2f}, indicating "
                f"{'high' if entropy > 0.5 else 'low'} uncertainty in its visual focus.")
