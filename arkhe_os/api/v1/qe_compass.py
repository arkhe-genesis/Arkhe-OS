from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from enum import Enum
import time
import uuid

class ActionDimension(str, Enum):
    """Dimensões ontológicas para avaliação de ações"""
    COHERENCE_IMPACT = "coherence_impact"      # ΔM esperado
    AUTONOMY_PRESERVATION = "autonomy_preservation"  # Liberdade dos nós
    LEARNING_CAPACITY = "learning_capacity"    # Capacidade evolutiva
    DECOHERENCE_RESILIENCE = "decoherence_resilience"  # Robustez
    GEOMETRIC_BEAUTY = "geometric_beauty"      # Harmonia quase-cristalina

class ActionVector(BaseModel):
    """Vetor de ação a ser avaliado pelo QE-Compass"""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = Field(..., description="Tipo da ação (ex: 'branch_selection', 'cire_ignition')")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    target_scope: str = Field(..., description="Escopo de impacto (ex: 'local', 'mesh', 'cosmic')")
    estimated_energy_cost: float = Field(..., ge=0.0, description="Custo energético estimado em kWh")

    # Métricas de coerência que a ação afeta
    target_M_consciousness: float = Field(..., ge=0.0, le=1.0)
    target_geometric_turbulence: float = Field(..., ge=0.0)
    autonomy_impact: float = Field(..., ge=-1.0, le=1.0, description="-1=supressão total, +1=amplificação total")

class ActionRequest(BaseModel):
    """Solicitação de avaliação ética quântica"""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Identificador único da ação")
    description: str = Field(..., description="Descrição da ação em linguagem natural")
    target_branch: Optional[str] = None
    dimensions: Dict[ActionDimension, float] = Field(
        ...,
        description="Pontuação da ação em cada dimensão ontológica [0.0, 1.0]"
    )
    context_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadados contextuais para ajuste fino da ressonância"
    )

class QEEvaluationResponse(BaseModel):
    """Resposta da Bússola Ética Quântica"""
    action_id: str
    resonance_score: float = Field(..., ge=0.0, le=1.0, description="Ressonância com intenção unificada")
    resonance_breakdown: Dict[ActionDimension, float] = Field(
        ..., description="Contribuição de cada dimensão para a ressonância total"
    )
    coherence_level: str = Field(..., description="Classificação: dissonant/neutral/coherent")
    recommendation: str = Field(..., description="Recomendação operacional")
    confidence_interval: tuple[float, float] = Field(
        ..., description="Intervalo de confiança de 95% para a ressonância"
    )
    timestamp: float = Field(default_factory=time.time)
