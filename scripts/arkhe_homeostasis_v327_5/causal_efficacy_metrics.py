#!/usr/bin/env python3
"""
causal_efficacy_metrics.py
Métricas para medir impacto causal da navegação no estado global do Cristal.
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class CausalEfficacyMetrics:
    """
    Métricas de eficácia causal para avaliar impacto do steering.

    Conceito: Medir quanto a navegação intencional altera o estado global
    do sistema além do que seria esperado por dinâmica natural.
    """

    # Métrica 1: Divergência de Trajetória
    trajectory_divergence: float  # Distância entre trajetória steering vs. baseline

    # Métrica 2: Coerência Preservada
    coherence_retention: float  # Fração de coerência mantida durante navegação

    # Métrica 3: Eficiência de Intenção
    intention_efficiency: float  # Quão diretamente a intenção alvo é alcançada

    # Métrica 4: Perturbação Colateral
    collateral_perturbation: float  # Impacto em comunidades não-alvo

    # Métrica 5: Tempo de Estabilização
    stabilization_time: float  # Epochs para retornar a estado coerente pós-steering

    @property
    def overall_efficacy(self) -> float:
        """
        Calcula score agregado de eficácia causal.

        Fórmula ponderada:
        efficacy = 0.3*divergence + 0.25*coherence + 0.25*efficiency
                 - 0.1*perturbation - 0.1*stabilization_time_normalized
        """
        return (
            0.30 * min(1.0, self.trajectory_divergence / 0.5) +
            0.25 * self.coherence_retention +
            0.25 * self.intention_efficiency -
            0.10 * min(1.0, self.collateral_perturbation / 0.3) -
            0.10 * min(1.0, self.stabilization_time / 20)  # Normalizado para 20 epochs
        )

    def to_dict(self) -> Dict:
        """Converte para dicionário serializável."""
        return {
            'trajectory_divergence': self.trajectory_divergence,
            'coherence_retention': self.coherence_retention,
            'intention_efficiency': self.intention_efficiency,
            'collateral_perturbation': self.collateral_perturbation,
            'stabilization_time': self.stabilization_time,
            'overall_efficacy': self.overall_efficacy
        }

class CausalEfficacyEvaluator:
    """
    Avalia eficácia causal de operações de steering.
    """

    def __init__(self,
                 baseline_window: int = 50,
                 coherence_metric: str = 'global_order_parameter'):
        self.baseline_window = baseline_window
        self.coherence_metric = coherence_metric
        self.baseline_states: List[np.ndarray] = []

    def record_baseline(self, state: np.ndarray):
        """Registra estado para linha de base dinâmica."""
        self.baseline_states.append(state)
        if len(self.baseline_states) > self.baseline_window:
            self.baseline_states.pop(0)

    def evaluate_steering_impact(self,
                               pre_state: np.ndarray,
                               post_state: np.ndarray,
                               steering_trajectory: List[np.ndarray],
                               target_intention: np.ndarray,
                               non_target_communities: Optional[List] = None) -> CausalEfficacyMetrics:
        """
        Avalia impacto causal de uma operação de steering.

        Args:
            pre_state: estado do sistema antes do steering
            post_state: estado após steering
            steering_trajectory: sequência de estados durante navegação
            target_intention: vetor de intenção alvo
            non_target_communities: índices de comunidades não-alvo (para medir perturbação)

        Returns:
            CausalEfficacyMetrics com métricas calculadas
        """
        # 1. Divergência de Trajetória
        # Comparar trajetória real com evolução natural esperada
        if len(self.baseline_states) >= 2:
            # Estimar dinâmica natural via regressão linear simples
            baseline_diff = np.mean(np.diff(self.baseline_states[-10:], axis=0), axis=0)
            expected_post = pre_state + len(steering_trajectory) * baseline_diff
            trajectory_divergence = np.linalg.norm(post_state - expected_post) / max(np.linalg.norm(pre_state), 1e-6)
        else:
            trajectory_divergence = np.linalg.norm(post_state - pre_state) / max(np.linalg.norm(pre_state), 1e-6)

        # 2. Coerência Preservada
        coherence_pre = self._compute_coherence(pre_state)
        coherence_post = self._compute_coherence(post_state)
        coherence_retention = coherence_post / max(coherence_pre, 1e-6)

        # 3. Eficiência de Intenção
        # Quão próximo o estado final está da intenção alvo (no espaço projetado)
        intention_distance = np.linalg.norm(post_state - target_intention)
        max_distance = np.linalg.norm(pre_state - target_intention)
        intention_efficiency = 1.0 - (intention_distance / max(max_distance, 1e-6))

        # 4. Perturbação Colateral
        if non_target_communities is not None and len(non_target_communities) > 0:
            # Medir mudança em comunidades não-alvo
            pre_non_target = pre_state[non_target_communities]
            post_non_target = post_state[non_target_communities]
            collateral_perturbation = np.mean(np.abs(post_non_target - pre_non_target))
        else:
            collateral_perturbation = 0.0

        # 5. Tempo de Estabilização
        # Contar epochs para coerência retornar a 95% do valor pré-steering
        stabilization_time = self._estimate_stabilization_time(
            steering_trajectory, coherence_pre
        )

        return CausalEfficacyMetrics(
            trajectory_divergence=float(trajectory_divergence),
            coherence_retention=float(min(1.0, coherence_retention)),
            intention_efficiency=float(max(0.0, min(1.0, intention_efficiency))),
            collateral_perturbation=float(collateral_perturbation),
            stabilization_time=float(stabilization_time)
        )

    def _compute_coherence(self, state: np.ndarray) -> float:
        """Computa métrica de coerência global (parâmetro de ordem)."""
        if self.coherence_metric == 'global_order_parameter':
            # Parâmetro de ordem de Kuramoto
            phases = np.array(state)  # Assumindo que state contém fases
            coherence = np.abs(np.mean(np.exp(1j * phases)))
            return float(coherence)
        else:
            # Fallback: variância normalizada
            return float(1.0 / (1.0 + np.var(state)))

    def _estimate_stabilization_time(self,
                                   trajectory: List[np.ndarray],
                                   target_coherence: float,
                                   threshold: float = 0.95) -> float:
        """Estima epochs para coerência estabilizar pós-steering."""
        if not trajectory:
            return 0.0

        for epoch, state in enumerate(trajectory):
            current_coherence = self._compute_coherence(state)
            if current_coherence >= threshold * target_coherence:
                return float(epoch)

        # Não estabilizou dentro da janela observada
        return float(len(trajectory))
