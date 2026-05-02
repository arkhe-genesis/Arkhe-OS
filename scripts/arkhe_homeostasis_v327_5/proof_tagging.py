#!/usr/bin/env python3
"""
proof_tagging.py
Sistema de tagging para distinguir tipos de prova na cadeia de coerência.
"""
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import json

class ProofType(Enum):
    """Tipos de prova na cadeia de coerência."""

    # Provas de monitoramento (baixo limiar, observação contínua)
    TORSIONAL_STABILITY = auto()      # Estabilidade torsional de camadas
    GEOMETRY_MONITORING = auto()      # CAPTURE 30-80%: observação de estrutura
    COHERENCE_TRACKING = auto()        # Mudanças graduais em ρ ou dimensão

    # Provas de certificação (alto limiar, afirmação forte)
    COHERENCE_CERTIFICATION = auto()   # CAPTURE ≥80%: certificação de coerência
    MANIFOLD_VALIDATION = auto()       # Validação formal de estrutura do manifold

    # Provas de evento (disparadas por condições específicas)
    REGIME_TRANSITION = auto()         # Mudança de CAPTURE↔SHATTERING↔DILUTION
    PARAMETER_OPTIMIZATION = auto()    # Após ajuste significativo de κ, λ, etc.

    # Provas de sistema
    SYSTEM_HEARTBEAT = auto()          # Prova periódica de integridade do sistema
    ERROR_RECOVERY = auto()            # Após recuperação de falha

@dataclass
class ProofMetadata:
    """Metadados enriquecidos para provas taggeadas."""

    proof_type: ProofType
    priority: str  # 'low', 'medium', 'high', 'critical'

    # Gatilhos
    triggered_by: str  # e.g., "threshold_crossed", "epoch_milestone", "manual_request"

    # Contexto da prova
    capture_fraction: float
    cohesion_rho: Optional[float] = None
    manifold_dimension: Optional[int] = None

    threshold_value: Optional[float] = None

    # Impacto esperado
    downstream_actions: List[str] = field(default_factory=list)

    # Para verificação independente
    verification_hints: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Converte para dicionário serializável."""
        return {
            'proof_type': self.proof_type.name,
            'priority': self.priority,
            'context': {
                'capture_fraction': self.capture_fraction,
                'cohesion_rho': self.cohesion_rho,
                'manifold_dimension': self.manifold_dimension
            },
            'triggers': {
                'triggered_by': self.triggered_by,
                'threshold_value': self.threshold_value
            },
            'impact': {
                'downstream_actions': self.downstream_actions
            },
            'verification': self.verification_hints
        }

class ProofTagger:
    """
    Classifica e taggeia provas baseado em contexto e limiares.
    """

    def __init__(self,
                 monitoring_threshold: float = 0.30,
                 certification_threshold: float = 0.80,
                 transition_sensitivity: float = 0.15):
        self.monitoring_threshold = monitoring_threshold
        self.certification_threshold = certification_threshold
        self.transition_sensitivity = transition_sensitivity
        self.previous_state: Optional[Dict] = None

    def classify_proof(self,
                     capture_fraction: float,
                     cohesion_rho: Optional[float] = None,
                     manifold_dim: Optional[int] = None,
                     epoch: Optional[int] = None,
                     torsional_coherence: Optional[float] = None,
                     parameter_change: Optional[Dict] = None) -> ProofMetadata:
        """
        Classifica tipo de prova baseado em contexto.

        Args:
            capture_fraction: fração de cristais em regime CAPTURE
            cohesion_rho: coesão da comunidade dominante
            manifold_dim: dimensionalidade estimada do manifold
            epoch: número da epoch atual (para detecção de milestones)
            parameter_change: dict com mudanças de parâmetros (se aplicável)

        Returns:
            ProofMetadata com classificação e metadados
        """
        # Detectar transição de regime
        regime_transition = False
        if self.previous_state and capture_fraction is not None:
            prev_capture = self.previous_state.get('capture_fraction')
            if prev_capture is not None:
                delta = abs(capture_fraction - prev_capture)
                if delta >= self.transition_sensitivity:
                    regime_transition = True

        # Atualizar estado anterior
        self.previous_state = {
            'capture_fraction': capture_fraction,
            'cohesion_rho': cohesion_rho,
            'epoch': epoch
        }

        # Lógica de classificação
        if torsional_coherence is not None and torsional_coherence >= self.certification_threshold:
            proof_type = ProofType.TORSIONAL_STABILITY
            priority = 'high'
            triggered_by = 'torsional_threshold'
            threshold_value = self.certification_threshold
            downstream = ['verify_torsional_stability']

        elif capture_fraction >= self.certification_threshold:
            proof_type = ProofType.COHERENCE_CERTIFICATION
            priority = 'high'
            triggered_by = 'threshold_crossed'
            threshold_value = self.certification_threshold
            downstream = ['submit_to_octra', 'publish_evidence', 'enable_steering']

        elif capture_fraction >= self.monitoring_threshold:
            proof_type = ProofType.GEOMETRY_MONITORING
            priority = 'medium'
            triggered_by = 'continuous_observation'
            threshold_value = self.monitoring_threshold
            downstream = ['log_for_analysis', 'update_dashboard']

        elif regime_transition:
            proof_type = ProofType.REGIME_TRANSITION
            priority = 'high'
            triggered_by = 'regime_change_detected'
            threshold_value = None
            downstream = ['alert_researcher', 're_evaluate_parameters']

        elif parameter_change and any(abs(v) > 0.1 for v in parameter_change.values()):
            proof_type = ProofType.PARAMETER_OPTIMIZATION
            priority = 'medium'
            triggered_by = 'parameter_adjustment'
            threshold_value = None
            downstream = ['validate_new_configuration']

        elif epoch and epoch % 10 == 0:
            proof_type = ProofType.SYSTEM_HEARTBEAT
            priority = 'low'
            triggered_by = 'epoch_milestone'
            threshold_value = None
            downstream = ['system_health_check']

        else:
            # Fallback: monitoramento de baixo nível
            proof_type = ProofType.COHERENCE_TRACKING
            priority = 'low'
            triggered_by = 'continuous_tracking'
            threshold_value = None
            downstream = ['append_to_timeline']

        # Construir metadados
        return ProofMetadata(
            proof_type=proof_type,
            priority=priority,
            capture_fraction=capture_fraction,
            cohesion_rho=cohesion_rho,
            manifold_dimension=manifold_dim,
            triggered_by=triggered_by,
            threshold_value=threshold_value,
            downstream_actions=downstream,
            verification_hints={
                'expected_capture_range': (
                    (self.monitoring_threshold, 1.0) if proof_type == ProofType.COHERENCE_CERTIFICATION
                    else (0.0, self.certification_threshold)
                ),
                'cohesion_consistency': abs(cohesion_rho) > 0.5 if cohesion_rho is not None else None
            }
        )
