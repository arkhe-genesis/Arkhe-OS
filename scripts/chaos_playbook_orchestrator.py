# chaos_playbook_orchestrator.py — Orquestrador da sinfonia de caos

import asyncio
import time
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict

# Mock imports from local scripts
from chaos_injector import ChaosInjector, InjectionDefinition, InjectionType, InjectionResult
from chaos_oracles import OracleEvaluator, OracleResult

class ExperimentPhase(Enum):
    """Fases do playbook de caos."""
    WARMUP = auto()
    STRESS = auto()
    RESISTANCE = auto()
    SURVIVAL = auto()
    CONSECRATION = auto()

@dataclass
class PlaybookExperiment:
    """Definição de um experimento no playbook."""
    experiment_id: str
    phase: ExperimentPhase
    definition: InjectionDefinition
    dependencies: List[str] = field(default_factory=list)
    parallel_group: Optional[str] = None
    min_omega_before: float = 0.9
    recovery_wait_s: float = 10 # Reduced for simulation

@dataclass
class PlaybookResult:
    """Resultado completo da execução do playbook."""
    start_time: float
    end_time: float
    experiments_executed: int
    experiments_passed: int
    experiments_failed: int
    phases_completed: List[ExperimentPhase]
    overall_verdict: bool
    details: Dict[str, any] = field(default_factory=dict)

class ChaosPlaybookOrchestrator:
    """
    Orquestrador temporal do playbook de caos.
    """

    def __init__(self, injector: ChaosInjector, oracles: OracleEvaluator):
        self.injector = injector
        self.oracles = oracles
        self.results: Dict[str, any] = {}
        self.completed_experiments: Set[str] = set()

        # Define the Playbook DAG
        self.PLAYBOOK: List[PlaybookExperiment] = [
            PlaybookExperiment("H1", ExperimentPhase.WARMUP,
                              InjectionDefinition("kill_quantum_pods", InjectionType.POD_KILL, {"app": "quantum-operator"}, {"percent": 30}, 60, "namespace")),
            PlaybookExperiment("N2", ExperimentPhase.WARMUP,
                              InjectionDefinition("latency_spike", InjectionType.LATENCY_INJECTION, {"region": "sa-east-1"}, {"latency_ms": 500}, 180, "region")),
            PlaybookExperiment("H2", ExperimentPhase.STRESS,
                              InjectionDefinition("cpu_stress", InjectionType.CPU_STRESS, {"app": "guardian-operator"}, {"cpu": 4}, 120, "namespace"), dependencies=["H1"]),
        ]

    async def execute_playbook(self) -> PlaybookResult:
        start_time = time.time()
        phases_completed = []
        overall_success = True

        for phase in ExperimentPhase:
            if phase == ExperimentPhase.CONSECRATION: continue

            logging.info(f"[PLAYBOOK] Iniciando Fase: {phase.name}")
            phase_experiments = [e for e in self.PLAYBOOK if e.phase == phase]

            if not phase_experiments: continue

            ready_experiments = [
                e for e in phase_experiments
                if all(dep in self.completed_experiments for dep in e.dependencies)
            ]

            for exp in ready_experiments:
                success = await self._execute_single_experiment(exp)
                if not success:
                    overall_success = False

            phases_completed.append(phase)

        return PlaybookResult(
            start_time=start_time,
            end_time=time.time(),
            experiments_executed=len(self.completed_experiments),
            experiments_passed=sum(1 for r in self.results.values() if r.get('success')),
            experiments_failed=len(self.completed_experiments) - sum(1 for r in self.results.values() if r.get('success')),
            phases_completed=phases_completed,
            overall_verdict=overall_success
        )

    async def _execute_single_experiment(self, exp: PlaybookExperiment) -> bool:
        logging.info(f"[PLAYBOOK] Executando {exp.experiment_id}...")

        async with self.injector.inject_context(exp.definition) as injection_result:
            # Evaluate oracles
            evals = await self.oracles.evaluate_experiment_oracles(
                exp.experiment_id,
                ["omega_recovery"],
                {"omega_recovery": 0.98},
                time.time()
            )
            success, reason = self.oracles.get_experiment_verdict(evals)

            self.results[exp.experiment_id] = {
                "success": success,
                "reason": reason,
                "injection": injection_result
            }

            if success:
                self.completed_experiments.add(exp.experiment_id)
                await asyncio.sleep(exp.recovery_wait_s)
                return True
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    injector = ChaosInjector()
    oracles = OracleEvaluator("http://prometheus")
    orchestrator = ChaosPlaybookOrchestrator(injector, oracles)
    asyncio.run(orchestrator.execute_playbook())
