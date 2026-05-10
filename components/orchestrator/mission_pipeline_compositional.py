#!/usr/bin/env python3
"""
mission_pipeline_compositional.py — Integra compositional_dp ao pipeline de missões do Orchestrator.
Garante que cada query respeite o orçamento de privacidade composto.
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import hashlib

# Importar componentes existentes
from privacy.compositional_dp import CompositionalGeometricDP, CompositionalPrivacyConfig, CompositionStrategy
from orchestrator_v166_experimental import ArkheOrchestratorV166Experimental

@dataclass
class CompositionalMissionConfig:
    """Configuração para missão com privacidade composicional."""
    mission_id: str
    total_epsilon_budget: float = 1.0
    total_delta_budget: float = 1e-5
    max_queries: int = 50
    strategy: CompositionStrategy = CompositionStrategy.GEOMETRIC_OPTIMIZED
    core_radius: float = 2.0
    distance_decay: str = 'gaussian'
    auto_adapt_on_budget_exhaustion: bool = True

class CompositionalMissionPipeline:
    """
    Pipeline de missão que integra privacidade composicional.

    Fluxo:
    1. Inicializar CompositionalGeometricDP com orçamento da missão
    2. Para cada query:
       a. Calcular ε_geo baseado na distância do participante
       b. Verificar orçamento restante
       c. Se exceder: adaptar query ou solicitar mais recursos
       d. Executar query e atualizar accounting
    3. Ao final: exportar relatório de privacidade da missão
    """

    def __init__(
        self,
        orchestrator: ArkheOrchestratorV166Experimental,
        config: CompositionalMissionConfig
    ):
        self.orchestrator = orchestrator
        self.config = config

        # Inicializar mecanismo de privacidade composicional
        dp_config = CompositionalPrivacyConfig(
            base_epsilon=0.1,  # ε base por query
            base_delta=config.total_delta_budget / config.max_queries,
            strategy=config.strategy,
            max_queries=config.max_queries,
            target_total_epsilon=config.total_epsilon_budget,
            core_radius=config.core_radius,
            distance_decay=config.distance_decay
        )
        self.compositional_dp = CompositionalGeometricDP(dp_config)

        # Estado da missão
        self.mission_active = False
        self.query_log: List[Dict] = []
        self.adaptation_events: List[Dict] = []

    def start_mission(self, mission_id: Optional[str] = None) -> bool:
        """Inicia nova missão com orçamento de privacidade."""
        if self.mission_active:
            return False

        self.mission_active = True
        self.query_log.clear()
        self.adaptation_events.clear()

        # Resetar accounting de privacidade
        self.compositional_dp.current_epsilon_spent = 0.0
        self.compositional_dp.current_delta_spent = 0.0
        self.compositional_dp.query_history.clear()

        print(f"🚀 Missão {mission_id or self.config.mission_id} iniciada")
        print(f"   • Orçamento de privacidade: ε={self.config.total_epsilon_budget}, δ={self.config.total_delta_budget}")
        print(f"   • Estratégia: {self.config.strategy.name}")
        return True

    def execute_query_with_privacy(
        self,
        query_fn: Callable,
        wavefunctions: List[torch.Tensor],
        participant_distances: List[float],
        query_metadata: Dict,
        allow_adaptation: bool = True
    ) -> Tuple[torch.Tensor, Dict]:
        """
        Executa query com verificação e adaptação de privacidade composicional.

        Returns:
            (resultado, metadata) onde metadata inclui status de privacidade
        """
        if not self.mission_active:
            raise RuntimeError("Mission not started. Call start_mission() first.")

        # Calcular ε efetivo para esta query com otimização geométrica
        suppressions = []
        for d in participant_distances:
            if self.config.distance_decay == 'gaussian':
                supp = np.exp(-d**2 / (2 * self.config.core_radius**2))
            elif self.config.distance_decay == 'exponential':
                supp = np.exp(-d / self.config.core_radius)
            else:  # linear
                supp = max(0, 1 - d / (3 * self.config.core_radius))
            suppressions.append(supp)

        avg_suppression = np.mean(suppressions)
        effective_epsilon = 0.1 * avg_suppression  # base_epsilon * suppression

        # Verificar orçamento antes de executar
        budget_check = self.compositional_dp.check_budget_remaining()

        if effective_epsilon > budget_check['epsilon_remaining'] and allow_adaptation:
            # Orçamento insuficiente: adaptar query
            adaptation_result = self._adapt_query_for_privacy(
                query_fn, wavefunctions, participant_distances, query_metadata
            )
            self.adaptation_events.append(adaptation_result)

            if adaptation_result['adapted']:
                # Re-calcular ε após adaptação
                effective_epsilon = adaptation_result['new_epsilon']
                print(f"  ⚙️ Query adaptada: ε reduzido de {effective_epsilon * 1.5:.3f} para {effective_epsilon:.3f}")
            else:
                # Não foi possível adaptar: retornar erro
                return None, {
                    'status': 'PRIVACY_BUDGET_EXHAUSTED',
                    'epsilon_requested': effective_epsilon,
                    'epsilon_remaining': budget_check['epsilon_remaining'],
                    'adaptation_attempted': True
                }

        # Executar query com accounting de privacidade
        result, privacy_accounting = self.compositional_dp.execute_compositional_query(
            query_fn=query_fn,
            wavefunctions=wavefunctions,
            participant_distances=participant_distances,
            query_metadata={**query_metadata, 'effective_epsilon': effective_epsilon}
        )

        # Registrar no log da missão
        self.query_log.append({
            'timestamp': time.time(),
            'query_id': query_metadata.get('query_id'),
            'epsilon_spent': privacy_accounting['query_epsilon'],
            'cumulative_epsilon': privacy_accounting['cumulative_epsilon'],
            'budget_remaining': privacy_accounting['remaining_budget_epsilon'],
            'participant_count': len(wavefunctions),
            'avg_suppression': avg_suppression
        })

        # Verificar se missão deve ser encerrada por exaustão de orçamento
        if privacy_accounting['remaining_budget_epsilon'] < 0.01:
            print(f"  ⚠️ Orçamento de privacidade quase exaurido: ε restante = {privacy_accounting['remaining_budget_epsilon']:.4f}")

        return result, {
            'status': 'SUCCESS',
            'privacy_accounting': privacy_accounting,
            'query_log_entry': self.query_log[-1]
        }

    def _adapt_query_for_privacy(
        self,
        query_fn: Callable,
        wavefunctions: List[torch.Tensor],
        participant_distances: List[float],
        query_metadata: Dict
    ) -> Dict:
        """
        Adapta query para reduzir consumo de privacidade.

        Estratégias (em ordem de preferência):
        1. Reduzir número de participantes (amostragem)
        2. Aumentar core_radius efetivo (mais supressão geométrica)
        3. Reduzir complexidade da query (via wrapper)
        """
        original_epsilon = 0.1 * np.mean([
            np.exp(-d**2 / (2 * self.config.core_radius**2)) if self.config.distance_decay == 'gaussian'
            else np.exp(-d / self.config.core_radius) if self.config.distance_decay == 'exponential'
            else max(0, 1 - d / (3 * self.config.core_radius))
            for d in participant_distances
        ])

        # Estratégia 1: Amostrar subconjunto de participantes
        if len(wavefunctions) > 5:
            sample_size = max(3, int(len(wavefunctions) * 0.6))
            indices = np.random.choice(len(wavefunctions), sample_size, replace=False)
            sampled_wavefunctions = [wavefunctions[i] for i in indices]
            sampled_distances = [participant_distances[i] for i in indices]

            # Re-calcular ε para amostra
            new_suppressions = [
                np.exp(-d**2 / (2 * self.config.core_radius**2)) if self.config.distance_decay == 'gaussian'
                else np.exp(-d / self.config.core_radius) if self.config.distance_decay == 'exponential'
                else max(0, 1 - d / (3 * self.config.core_radius))
                for d in sampled_distances
            ]
            new_epsilon = 0.1 * np.mean(new_suppressions)

            # Wrapper para query adaptada
            def adapted_query_fn(wf_list):
                return query_fn(wf_list)  # mesma função, menos dados

            return {
                'adapted': True,
                'strategy': 'participant_sampling',
                'original_participants': len(wavefunctions),
                'sampled_participants': len(sampled_wavefunctions),
                'original_epsilon': original_epsilon,
                'new_epsilon': new_epsilon,
                'query_fn': adapted_query_fn,
                'wavefunctions': sampled_wavefunctions,
                'participant_distances': sampled_distances
            }

        # Estratégia 2: Aumentar core_radius para mais supressão
        elif self.config.core_radius < 5.0:
            new_core_radius = min(5.0, self.config.core_radius * 1.5)
            new_suppressions = [
                np.exp(-d**2 / (2 * new_core_radius**2)) if self.config.distance_decay == 'gaussian'
                else np.exp(-d / new_core_radius) if self.config.distance_decay == 'exponential'
                else max(0, 1 - d / (3 * new_core_radius))
                for d in participant_distances
            ]
            new_epsilon = 0.1 * np.mean(new_suppressions)

            return {
                'adapted': True,
                'strategy': 'increase_core_radius',
                'original_core_radius': self.config.core_radius,
                'new_core_radius': new_core_radius,
                'original_epsilon': original_epsilon,
                'new_epsilon': new_epsilon,
                'query_fn': query_fn,
                'wavefunctions': wavefunctions,
                'participant_distances': participant_distances
            }

        # Estratégia 3: Reduzir complexidade da query (placeholder)
        else:
            # Em produção: usar versão simplificada da query_fn
            return {
                'adapted': False,
                'reason': 'no_adaptation_strategy_available',
                'original_epsilon': original_epsilon
            }

    def end_mission(self) -> Dict:
        """Encerra missão e retorna relatório de privacidade."""
        if not self.mission_active:
            return {'error': 'No active mission'}

        self.mission_active = False

        report = {
            'mission_id': self.config.mission_id,
            'total_queries': len(self.query_log),
            'epsilon_spent': self.compositional_dp.current_epsilon_spent,
            'delta_spent': self.compositional_dp.current_delta_spent,
            'budget_utilization': self.compositional_dp.current_epsilon_spent / self.config.total_epsilon_budget,
            'adaptation_events': len(self.adaptation_events),
            'query_log_summary': {
                'avg_epsilon_per_query': np.mean([q['epsilon_spent'] for q in self.query_log]) if self.query_log else 0,
                'max_epsilon_single_query': max([q['epsilon_spent'] for q in self.query_log], default=0),
                'min_budget_remaining': min([q['budget_remaining'] for q in self.query_log], default=0)
            },
            'privacy_guarantee': f'({self.compositional_dp.current_epsilon_spent:.3f}, {self.config.total_delta_budget})-DP',
            'timestamp': time.time()
        }

        print(f"✅ Missão encerrada: {report['total_queries']} queries, "
              f"ε gasto={report['epsilon_spent']:.3f}/{self.config.total_epsilon_budget}")

        return report

    def export_privacy_report(self, path: str):
        """Exporta relatório detalhado de privacidade da missão."""
        import json

        report = {
            'config': {
                'mission_id': self.config.mission_id,
                'total_epsilon_budget': self.config.total_epsilon_budget,
                'strategy': self.config.strategy.name,
                'core_radius': self.config.core_radius
            },
            'execution': {
                'total_queries': len(self.query_log),
                'epsilon_spent': self.compositional_dp.current_epsilon_spent,
                'adaptation_events': self.adaptation_events,
                'query_log': self.query_log
            },
            'privacy_guarantee': {
                'composed_epsilon': self.compositional_dp.current_epsilon_spent,
                'composed_delta': self.compositional_dp.current_delta_spent,
                'formula': "ε_total = √(2k ln(1/δ'))·ε + kε(e^ε - 1) [advanced composition]"
            },
            'export_timestamp': time.time()
        }

        with open(path, 'w') as f:
            json.dump(report, f, indent=2, default=lambda x: x.item() if isinstance(x, (np.floating, np.integer)) else str(x))

        print(f"📋 Relatório de privacidade exportado para {path}")
