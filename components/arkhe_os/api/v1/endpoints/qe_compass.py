from fastapi import APIRouter, HTTPException, Depends
import time
import numpy as np
from typing import Dict, Optional, Tuple, List
from sqlalchemy.orm import Session

from arkhe_os.api.v1.qe_compass import ActionRequest, QEEvaluationResponse, ActionDimension
from arkhe_os.core.scaffold import ScaffoldState
from arkhe_os.db.session import get_db
from arkhe_os.auth.dependencies import get_current_active_user, RoleChecker
from arkhe_os.models.user import User, UserRole
from arkhe_os.models.arkhe_models import Intention

router = APIRouter(tags=["QE-Compass"])

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
    resonance = sum(
        weights[dim] * action_dims[dim] * intention_vector[dim]
        for dim in ActionDimension
    )
    if context and context.get("emergency", False):
        weights_adj = weights.copy()
        weights_adj[ActionDimension.COHERENCE_IMPACT] *= 1.5
        total = sum(weights_adj.values())
        weights_adj = {k: v/total for k, v in weights_adj.items()}
        resonance = sum(
            weights_adj[dim] * action_dims[dim] * intention_vector[dim]
            for dim in ActionDimension
        )
    breakdown = {
        dim: weights[dim] * action_dims[dim] * intention_vector[dim]
        for dim in ActionDimension
    }
    max_possible = sum(weights.values())
    resonance = np.clip(resonance / max_possible, 0.0, 1.0)
    return float(resonance), breakdown

def get_scaffold_state():
    raise NotImplementedError("Scaffold state must be provided by dependency injection")

@router.post("/evaluate", response_model=QEEvaluationResponse)
async def evaluate_action(
    request: ActionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Avalia a ressonância de uma ação com a intenção unificada da Catedral.
    Requer autenticação.
    """
    resonance, breakdown = calculate_resonance(
        request.dimensions,
        INTENTION_VECTOR,
        ONTOLOGICAL_WEIGHTS,
        request.context_metadata
    )

    coherence_level = "coherent" if resonance >= 0.85 else "neutral" if resonance >= 0.60 else "dissonant"
    recommendation = "✅ EXECUTE" if resonance >= 0.85 else "🟡 REVIEW" if resonance >= 0.60 else "🔴 REJECT"

    # Persistir intenção no banco
    db_intention = Intention(
        user_id=current_user.id,
        intention_text=request.action_id, # Usando action_id como proxy
        resonance_score=resonance,
        status=coherence_level
    )
    db.add(db_intention)
    db.commit()

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
