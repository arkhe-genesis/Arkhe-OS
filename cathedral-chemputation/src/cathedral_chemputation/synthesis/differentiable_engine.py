"""
differentiable_engine.py — Differentiable Retrosynthesis Engine
Integra o modelo Transformer com scoring de acessibilidade sintética
"""

import torch
import torch.nn as nn
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from cathedral_chemputation.synthesis.transformer_model import (
    RetrosynthesisTransformer,
    ReactionPrediction,
)

@dataclass
class SyntheticPathway:
    """Rota sintética completa."""
    product_smiles: str
    steps: List[ReactionPrediction]
    overall_probability: float
    step_count: int
    cost_estimate: float
    synthesizability_score: float  # 0‑1

class DifferentiableRetrosynthesisEngine(nn.Module):
    """Motor de retrossíntese diferenciável."""

    def __init__(
        self,
        transformer: RetrosynthesisTransformer,
        tokenizer,
        max_steps: int = 5,
        temperature: float = 1.0,
    ):
        super().__init__()
        self.transformer = transformer
        self.tokenizer = tokenizer
        self.max_steps = max_steps
        self.temperature = temperature
        self.sa_scorer = SyntheticAccessibilityScorer()

    def forward(
        self,
        product_emb: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass diferenciável."""
        reactant_logits, gumbel_samples = self.transformer.differentiable_predict(
            product_emb, num_samples=5
        )

        synthesizability_score = self._compute_synthesizability_score(reactant_logits)
        return synthesizability_score, reactant_logits

    def _compute_synthesizability_score(self, logits: torch.Tensor) -> torch.Tensor:
        """Calcula score de sintetizabilidade a partir dos logits."""
        probs = torch.softmax(logits, dim=-1)
        entropy = -(probs * torch.log(probs + 1e-10)).sum(dim=-1).mean(dim=-1)
        score = 1.0 - entropy * 0.5
        return torch.sigmoid(score)

    def predict_pathway(
        self,
        product_smiles: str,
        max_steps: Optional[int] = None,
    ) -> List[SyntheticPathway]:
        """Prediz rotas sintéticas completas para um produto."""
        if max_steps is None:
            max_steps = self.max_steps

        pathways = self._beam_search_retrosynthesis(
            product_smiles=product_smiles,
            max_steps=max_steps,
            beam_width=5,
        )
        return pathways

    def _beam_search_retrosynthesis(
        self,
        product_smiles: str,
        max_steps: int,
        beam_width: int = 5,
    ) -> List[SyntheticPathway]:
        """Busca em feixe (beam search) para rotas retrossintéticas."""
        beam = [{
            "current_smiles": product_smiles,
            "steps": [],
            "log_prob": 0.0,
        }]

        for step in range(max_steps):
            new_beam = []
            for item in beam:
                predictions = self.transformer.predict_reactions(
                    product_smiles=item["current_smiles"],
                    tokenizer=self.tokenizer,
                    top_k=3,
                    temperature=self.temperature,
                )
                for pred in predictions:
                    for reactant in pred.reactants:
                        new_beam.append({
                            "current_smiles": reactant,
                            "steps": item["steps"] + [pred],
                            "log_prob": item["log_prob"] + math.log(pred.probability),
                        })
            new_beam.sort(key=lambda x: x["log_prob"], reverse=True)
            beam = new_beam[:beam_width]

        pathways = []
        for item in beam:
            pathways.append(SyntheticPathway(
                product_smiles=product_smiles,
                steps=item["steps"],
                overall_probability=math.exp(item["log_prob"]),
                step_count=len(item["steps"]),
                cost_estimate=100.0 * len(item["steps"]),
                synthesizability_score=self.sa_scorer.score(product_smiles, item["steps"]),
            ))
        return pathways


class SyntheticAccessibilityScorer:
    """Scorer de acessibilidade sintética."""
    def score(self, product_smiles: str, steps: List[ReactionPrediction]) -> float:
        step_penalty = max(0, 1.0 - 0.2 * len(steps))
        prob_score = 1.0
        for step in steps:
            prob_score *= step.probability
        return step_penalty * prob_score
