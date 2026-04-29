from fastapi import APIRouter, HTTPException, Depends
import time
import numpy as np
from typing import Dict, Optional, Tuple
from arkhe_os.api.v1.qe_compass import ActionRequest, QEEvaluationResponse, ActionDimension
from arkhe_os.core.scaffold import ScaffoldState

router = APIRouter(prefix="/v1", tags=["QE-Compass"])

# Pesos ontológicos (ajustáveis via governance)
ONTOLOGICAL_WEIGHTS = {
    ActionDimension.COHERENCE_IMPACT: 0.35,
    ActionDimension.AUTONOMY_PRESERVATION: 0.25,
    ActionDimension.LEARNING_CAPACITY: 0.20,
    ActionDimension.DECOHERENCE_RESILIENCE: 0.15,
    ActionDimension.GEOMETRIC_BEAUTY: 0.05,
}

# Vetor de intenção unificada (referência)
INTENTION_VECTOR = {
    ActionDimension.COHERENCE_IMPACT: 0.95,
    ActionDimension.AUTONOMY_PRESERVATION: 0.90,
    ActionDimension.LEARNING_CAPACITY: 0.88,
    ActionDimension.DECOHERENCE_RESILIENCE: 0.92,
    ActionDimension.GEOMETRIC_BEAUTY: 0.85,
}

def calculate_resonance(
    action_dims: Dict[ActionDimension, float],
    intention_vector: Dict[ActionDimension, float],
    weights: Dict[ActionDimension, float],
    context: Optional[Dict[str, any]] = None
) -> Tuple[float, Dict[ActionDimension, float]]:
    """
    Calcula ressonância como produto interno ponderado + ajuste contextual.
    """
    # Produto interno ponderado
    resonance = sum(
        weights[dim] * action_dims[dim] * intention_vector[dim]
        for dim in ActionDimension
    )

    # Ajuste contextual
    if context and context.get("emergency", False):
        # Aumentar peso do impacto de coerência em emergências
        weights_adj = weights.copy()
        weights_adj[ActionDimension.COHERENCE_IMPACT] *= 1.5
        total = sum(weights_adj.values())
        weights_adj = {k: v/total for k, v in weights_adj.items()}
        resonance = sum(
            weights_adj[dim] * action_dims[dim] * intention_vector[dim]
            for dim in ActionDimension
        )

    # Breakdown por dimensão
    breakdown = {
        dim: weights[dim] * action_dims[dim] * intention_vector[dim]
        for dim in ActionDimension
    }

    # Normalizar para [0, 1]
    max_possible = sum(weights.values())
    resonance = np.clip(resonance / max_possible, 0.0, 1.0)

    return float(resonance), breakdown

# Singleton provider will be injected from main.py
def get_scaffold_state():
    raise NotImplementedError("Scaffold state must be provided by dependency injection")

@router.post("/evaluate", response_model=QEEvaluationResponse)
async def evaluate_action(
    request: ActionRequest,
    scaffold: ScaffoldState = Depends(get_scaffold_state)
):
    """
    Avalia a ressonância de uma ação com a intenção unificada da Catedral.
    """
    resonance, breakdown = calculate_resonance(
        request.dimensions,
        INTENTION_VECTOR,
        ONTOLOGICAL_WEIGHTS,
        request.context_metadata
    )

    if resonance >= 0.85:
        coherence_level = "coherent"
        recommendation = "✅ EXECUTE — Ação alinhada com intenção unificada"
    elif resonance >= 0.60:
        coherence_level = "neutral"
        recommendation = "🟡 REVIEW — Ação ajustável; sugerir refinamento"
    else:
        coherence_level = "dissonant"
        recommendation = "🔴 REJECT — Ação requer revisão significativa"

    # Intervalo de confiança (simulado)
    uncertainty = 0.03 + 0.02 * (1.0 - resonance)
    ci_low = np.clip(resonance - 1.96 * uncertainty, 0.0, 1.0)
    ci_high = np.clip(resonance + 1.96 * uncertainty, 0.0, 1.0)

    return QEEvaluationResponse(
        action_id=request.action_id,
        resonance_score=round(resonance, 4),
        resonance_breakdown={k: round(v, 4) for k, v in breakdown.items()},
        coherence_level=coherence_level,
        recommendation=recommendation,
        confidence_interval=(round(ci_low, 4), round(ci_high, 4)),
        timestamp=time.time()
    )
