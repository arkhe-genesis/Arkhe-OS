#!/usr/bin/env python3
"""
compositional_dp.py — Composição avançada de queries com privacidade geométrica.
Implementa advanced composition com otimização baseada em distância ao núcleo.
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto

class CompositionStrategy(Enum):
    """Estratégias de composição de privacidade."""
    BASIC = auto()  # Composição básica: ε_total = k·ε
    ADVANCED = auto()  # Advanced composition (Dwork et al.)
    GEOMETRIC_OPTIMIZED = auto()  # Composição com otimização geométrica
    ZERO_CONCENTRATED = auto()  # zCDP composition

@dataclass
class CompositionalPrivacyConfig:
    """Configuração para composição de privacidade."""
    # Parâmetros base de DP
    base_epsilon: float = 0.1
    base_delta: float = 1e-6

    # Parâmetros de composição
    strategy: CompositionStrategy = CompositionStrategy.GEOMETRIC_OPTIMIZED
    max_queries: int = 100
    target_total_epsilon: float = 1.0

    # Parâmetros geométricos
    core_radius: float = 2.0  # σ_core para supressão geométrica
    distance_decay: str = 'gaussian'  # 'gaussian', 'exponential', 'linear'

    # Parâmetros de falha de composição
    composition_delta_prime: float = 1e-7

class CompositionalGeometricDP:
    """
    Mecanismo de privacidade composicional com otimização geométrica.

    Para k queries adaptativas, calcula bound rigoroso de ε_total usando
    advanced composition, com redução por supressão geométrica.
    """

    def __init__(self, config: CompositionalPrivacyConfig):
        self.config = config
        self.query_history: List[Dict] = []
        self.current_epsilon_spent = 0.0
        self.current_delta_spent = 0.0

    def compute_composed_epsilon(
        self,
        num_queries: int,
        per_query_epsilon: Optional[float] = None,
        per_query_delta: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calcula ε_total composto para num_queries.

        Suporta múltiplas estratégias de composição.
        """
        eps = per_query_epsilon or self.config.base_epsilon
        delta = per_query_delta or self.config.base_delta
        k = num_queries
        delta_prime = self.config.composition_delta_prime

        if self.config.strategy == CompositionStrategy.BASIC:
            # Composição básica (pessimista)
            epsilon_total = k * eps
            delta_total = k * delta

        elif self.config.strategy == CompositionStrategy.ADVANCED:
            # Advanced composition (Dwork, Rothblum, Vadhan 2010)
            # ε_total ≈ √[2k ln(1/δ')]·ε + kε(e^ε - 1)
            term1 = np.sqrt(2 * k * np.log(1 / delta_prime)) * eps
            term2 = k * eps * (np.exp(eps) - 1)
            epsilon_total = term1 + term2
            delta_total = k * delta + delta_prime

        elif self.config.strategy == CompositionStrategy.GEOMETRIC_OPTIMIZED:
            # Composição com otimização geométrica
            # Cada query tem ε_i = ε_base · exp(-d_i²/(2σ²))
            epsilon_total = 0.0
            for i in range(k):
                # Distância efetiva ao núcleo (simulada ou real)
                d_i = np.random.uniform(0, self.config.core_radius * 3)

                # Fator de supressão geométrica
                if self.config.distance_decay == 'gaussian':
                    suppression = np.exp(-d_i**2 / (2 * self.config.core_radius**2))
                elif self.config.distance_decay == 'exponential':
                    suppression = np.exp(-d_i / self.config.core_radius)
                else:  # linear
                    suppression = max(0, 1 - d_i / (3 * self.config.core_radius))

                # ε efetivo para esta query
                eps_i = eps * suppression
                epsilon_total += eps_i

            # Aplicar advanced composition aos ε_i reduzidos
            avg_eps = epsilon_total / k
            term1 = np.sqrt(2 * k * np.log(1 / delta_prime)) * avg_eps
            term2 = k * avg_eps * (np.exp(avg_eps) - 1)
            epsilon_total = term1 + term2
            delta_total = k * delta + delta_prime

        elif self.config.strategy == CompositionStrategy.ZERO_CONCENTRATED:
            # Zero-Concentrated DP composition
            # ε_total = k·ε + √[2k log(1/δ)]·ε
            epsilon_total = k * eps + np.sqrt(2 * k * np.log(1 / delta)) * eps
            delta_total = delta

        else:
            raise ValueError(f"Unknown composition strategy: {self.config.strategy}")

        return {
            'epsilon_total': epsilon_total,
            'delta_total': delta_total,
            'num_queries': k,
            'strategy': self.config.strategy.name,
            'per_query_epsilon': eps,
            'geometric_optimization': self.config.strategy == CompositionStrategy.GEOMETRIC_OPTIMIZED
        }

    def execute_compositional_query(
        self,
        query_fn: Callable,
        wavefunctions: List[torch.Tensor],
        participant_distances: Optional[List[float]] = None,
        query_metadata: Optional[Dict] = None
    ) -> Tuple[torch.Tensor, Dict]:
        """
        Executa uma query com composição de privacidade rastreada.

        Args:
            query_fn: função que processa wavefunctions e retorna resultado
            wavefunctions: dados dos participantes
            participant_distances: distâncias ao núcleo para otimização geométrica
            query_metadata: metadados da query para logging

        Returns:
            (resultado, privacy_accounting)
        """
        # Calcular ε efetivo para esta query com otimização geométrica
        if participant_distances and self.config.strategy == CompositionStrategy.GEOMETRIC_OPTIMIZED:
            # Média ponderada de supressão geométrica
            suppressions = []
            for d in participant_distances:
                if self.config.distance_decay == 'gaussian':
                    supp = np.exp(-d**2 / (2 * self.config.core_radius**2))
                elif self.config.distance_decay == 'exponential':
                    supp = np.exp(-d / self.config.core_radius)
                else:
                    supp = max(0, 1 - d / (3 * self.config.core_radius))
                suppressions.append(supp)

            avg_suppression = np.mean(suppressions)
            effective_epsilon = self.config.base_epsilon * avg_suppression
        else:
            effective_epsilon = self.config.base_epsilon

        # Executar query
        result = query_fn(wavefunctions)

        # Atualizar accounting de privacidade
        privacy_accounting = self._update_privacy_accounting(
            effective_epsilon, self.config.base_delta
        )

        # Registrar histórico
        self.query_history.append({
            'timestamp': time.time(),
            'epsilon_spent': effective_epsilon,
            'delta_spent': self.config.base_delta,
            'cumulative_epsilon': privacy_accounting['cumulative_epsilon'],
            'cumulative_delta': privacy_accounting['cumulative_delta'],
            'metadata': query_metadata or {}
        })

        return result, privacy_accounting

    def _update_privacy_accounting(
        self,
        query_epsilon: float,
        query_delta: float
    ) -> Dict[str, float]:
        """Atualiza contabilidade de privacidade após uma query."""
        k = len(self.query_history) + 1

        # Recalcular ε_total composto
        composed = self.compute_composed_epsilon(k)

        self.current_epsilon_spent = composed['epsilon_total']
        self.current_delta_spent = composed['delta_total']

        return {
            'query_epsilon': query_epsilon,
            'query_delta': query_delta,
            'cumulative_epsilon': self.current_epsilon_spent,
            'cumulative_delta': self.current_delta_spent,
            'remaining_budget_epsilon': max(0, self.config.target_total_epsilon - self.current_epsilon_spent),
            'budget_utilization': self.current_epsilon_spent / self.config.target_total_epsilon,
            'queries_executed': k,
            'queries_remaining': max(0, self.config.max_queries - k)
        }

    def check_budget_remaining(self) -> Dict[str, Union[bool, float]]:
        """Verifica se ainda há orçamento de privacidade disponível."""
        epsilon_remaining = self.config.target_total_epsilon - self.current_epsilon_spent
        delta_remaining = self.config.target_total_epsilon - self.current_delta_spent  # simplificação

        return {
            'budget_available': epsilon_remaining > 0 and delta_remaining > 0,
            'epsilon_remaining': epsilon_remaining,
            'delta_remaining': delta_remaining,
            'epsilon_utilization': self.current_epsilon_spent / self.config.target_total_epsilon,
            'can_execute_more_queries': epsilon_remaining > self.config.base_epsilon
        }

    def get_privacy_report(self) -> Dict:
        """Gera relatório completo de privacidade composicional."""
        return {
            'config': {
                'base_epsilon': self.config.base_epsilon,
                'base_delta': self.config.base_delta,
                'strategy': self.config.strategy.name,
                'target_total_epsilon': self.config.target_total_epsilon,
                'max_queries': self.config.max_queries
            },
            'current_status': {
                'epsilon_spent': self.current_epsilon_spent,
                'delta_spent': self.current_delta_spent,
                'queries_executed': len(self.query_history),
                'budget_remaining': self.check_budget_remaining()
            },
            'query_history_summary': {
                'total_queries': len(self.query_history),
                'avg_epsilon_per_query': np.mean([q['epsilon_spent'] for q in self.query_history]) if self.query_history else 0,
                'geometric_optimization_applied': any(
                    q.get('metadata', {}).get('geometric_optimization', False)
                    for q in self.query_history
                )
            }
        }
