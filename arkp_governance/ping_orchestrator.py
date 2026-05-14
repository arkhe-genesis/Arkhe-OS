#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ping_orchestrator.py — Substrato 189
Ping Orchestrator — Orquestrador de Intervenções Epistêmicas

Decide qual substrato recebe ping, com que intensidade, e em que frequência.
Usa um modelo de prioridade baseado em:
  • Urgência: Φ_C mais baixo = prioridade mais alta
  • Impacto: substratos com mais dependentes = prioridade mais alta
  • Histórico: substratos que já receberam pings recentes = prioridade mais baixa

O orquestrador garante que a Catedral gaste recursos de governança
eficientemente, maximizando o Φ_C global com o menor número de pings.
"""

import numpy as np
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto

from arkp_governance.spiral_ping_governor import SpiralPingGovernor, SubstrateHealth, SubstrateState
from arkp_governance.substrate_registry import SubstrateRegistry, SubstrateMetadata


class PriorityLevel(Enum):
    """Níveis de prioridade para ping."""
    CRITICAL = 1    # Φ_C < 0.90 ou π > 0.50
    HIGH = 2        # Φ_C < 0.95 ou π > 0.30
    MEDIUM = 3     # Tendência de queda de Φ_C
    LOW = 4         # Manutenção preventiva
    NONE = 5       # Saudável


@dataclass
class PingTask:
    """Tarefa de ping agendada."""
    substrate_id: str
    priority: PriorityLevel
    ping_intensity: float
    reason: str
    estimated_phi_c_gain: float
    estimated_pi_reduction: float


class PingOrchestrator:
    """
    Orquestrador de pings epistêmicos.

    Prioriza substratos comprometidos e otimiza a alocação de
    recursos de governança para maximizar Φ_C global.
    """

    def __init__(self, governor: SpiralPingGovernor, registry: SubstrateRegistry):
        self.governor = governor
        self.registry = registry
        self.task_queue: List[PingTask] = []
        self.max_pings_per_cycle = 3  # Limitar para evitar instabilidade
        self.cooldown_hours = 1.0      # Tempo mínimo entre pings no mesmo substrato

    def assess_priorities(self) -> List[PingTask]:
        """
        Avalia prioridades de ping para todos os substratos.

        Returns:
            Lista de tarefas de ping ordenadas por prioridade
        """
        tasks = []
        current_time = time.time()

        for substrate_id, health in self.governor.substrates.items():
            meta = self.registry.get(substrate_id)

            # Verificar cooldown
            if health.last_ping > 0 and (current_time - health.last_ping) < self.cooldown_hours * 3600:
                continue

            # Computar prioridade
            priority, reason = self._compute_priority(health, meta)

            if priority != PriorityLevel.NONE:
                # Computar intensidade do ping baseada na gravidade
                ping_intensity = self._compute_ping_intensity(health, priority)

                # Estimar ganhos
                est_phi_c_gain = self._estimate_phi_c_gain(health, ping_intensity)
                est_pi_reduction = self._estimate_pi_reduction(health, ping_intensity)

                task = PingTask(
                    substrate_id=substrate_id,
                    priority=priority,
                    ping_intensity=ping_intensity,
                    reason=reason,
                    estimated_phi_c_gain=est_phi_c_gain,
                    estimated_pi_reduction=est_pi_reduction,
                )
                tasks.append(task)

        # Ordenar por prioridade (menor número = mais urgente)
        tasks.sort(key=lambda t: t.priority.value)

        return tasks

    def _compute_priority(self, health: SubstrateHealth,
                          meta: Optional[SubstrateMetadata]) -> Tuple[PriorityLevel, str]:
        """Computa nível de prioridade para um substrato."""

        if health.state == SubstrateState.CRITICAL:
            return PriorityLevel.CRITICAL, f"Φ_C={health.phi_c:.3f} < 0.90 ou π={health.pi:.3f} > 0.50"

        elif health.state == SubstrateState.WARNING:
            return PriorityLevel.HIGH, f"Φ_C={health.phi_c:.3f} < 0.95 ou π={health.pi:.3f} > 0.30"

        elif health.phi_c < self.governor.phi_c_threshold + 0.02:
            # Próximo do limiar — manutenção preventiva
            return PriorityLevel.MEDIUM, f"Φ_C={health.phi_c:.3f} próximo do limiar"

        elif meta and len(meta.dependencies) > 3:
            # Substrato com muitas dependências — manutenção preventiva
            return PriorityLevel.LOW, f"Substrato crítico com {len(meta.dependencies)} dependências"

        else:
            return PriorityLevel.NONE, "Saudável"

    def _compute_ping_intensity(self, health: SubstrateHealth,
                                 priority: PriorityLevel) -> float:
        """Computa intensidade do ping baseada na prioridade."""
        base_intensity = {
            PriorityLevel.CRITICAL: 0.95,
            PriorityLevel.HIGH: 0.80,
            PriorityLevel.MEDIUM: 0.60,
            PriorityLevel.LOW: 0.40,
            PriorityLevel.NONE: 0.0,
        }

        intensity = base_intensity.get(priority, 0.5)

        # Ajustar baseado no histórico de pings
        if health.ping_count > 3:
            intensity *= 0.8  # Reduzir se já recebeu muitos pings

        # Ajustar baseado no π atual
        if health.pi > 0.7:
            intensity = min(0.99, intensity * 1.2)  # Aumentar para viés muito alto

        return float(np.clip(intensity, 0.1, 0.99))

    def _estimate_phi_c_gain(self, health: SubstrateHealth,
                              ping_intensity: float) -> float:
        """Estima ganho de Φ_C após ping."""
        # Modelo simplificado: ganho proporcional à distância do limiar
        gap = self.governor.phi_c_threshold - health.phi_c
        if gap <= 0:
            return 0.0

        # Ganho efetivo depende da intensidade do ping
        effective_gain = gap * ping_intensity * 0.8
        return float(np.clip(effective_gain, 0.0, 0.2))

    def _estimate_pi_reduction(self, health: SubstrateHealth,
                                ping_intensity: float) -> float:
        """Estima redução de π após ping."""
        # Modelo simplificado: redução proporcional ao π atual
        reduction = health.pi * ping_intensity * 0.5
        return float(np.clip(reduction, 0.0, 0.3))

    def execute_cycle(self) -> Dict[str, any]:
        """
        Executa ciclo de orquestração:
        1. Avaliar prioridades
        2. Selecionar substratos para ping
        3. Executar pings
        4. Retornar relatório
        """
        tasks = self.assess_priorities()

        # Selecionar top N tarefas
        selected_tasks = tasks[:self.max_pings_per_cycle]

        results = []
        for task in selected_tasks:
            try:
                intervention = self.governor.ping_substrate(
                    task.substrate_id,
                    task.ping_intensity
                )
                results.append({
                    'substrate': task.substrate_id,
                    'priority': task.priority.name,
                    'intensity': task.ping_intensity,
                    'phi_c_before': intervention.phi_c_before,
                    'phi_c_after': intervention.phi_c_after,
                    'pi_before': intervention.pi_before,
                    'pi_after': intervention.pi_after,
                    'seal': intervention.seal,
                })
            except Exception as e:
                results.append({
                    'substrate': task.substrate_id,
                    'error': str(e),
                })

        return {
            'tasks_assessed': len(tasks),
            'tasks_executed': len(selected_tasks),
            'results': results,
            'global_phi_c_after': self.governor.assess_global_health()['global_phi_c'],
        }

    def get_queue_status(self) -> List[Dict]:
        """Retorna status da fila de tarefas."""
        tasks = self.assess_priorities()
        return [
            {
                'substrate': t.substrate_id,
                'priority': t.priority.name,
                'intensity': t.ping_intensity,
                'reason': t.reason,
                'est_phi_c_gain': t.estimated_phi_c_gain,
                'est_pi_reduction': t.estimated_pi_reduction,
            }
            for t in tasks
        ]
