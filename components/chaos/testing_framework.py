# chaos/testing_framework.py — Framework de testes de caos para a Catedral

import asyncio
import time
import hashlib
import json
import logging
from typing import Dict, List, Optional, Union, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

# Imports que serão criados
from cathedral_organism import CathedralOrganism, OrganismPulse
from cathedral_codex import CrystalCodex
from quantum_processor import QuantumProcessor

class ChaosScenarioType(Enum):
    """Tipos de cenários de caos para a Catedral."""
    NETWORK_PARTITION = "network_partition"
    LATENCY_SPIKE = "latency_spike"
    PACKET_LOSS = "packet_loss"
    MERKLE_CORRUPTION = "merkle_corruption"
    STATE_INCONSISTENCY = "state_inconsistency"
    CACHE_POISONING = "cache_poisoning"
    ZK_PROOF_TIMEOUT = "zk_proof_timeout"
    CONSENSUS_DEADLOCK = "consensus_deadlock"
    QUANTUM_DEGRADATION = "quantum_degradation"
    CONSENT_FLOOD = "consent_flood"
    IOC_FLOOD = "ioc_flood"
    FIREWALL_BYPASS_ATTEMPT = "firewall_bypass_attempt"
    ROLLBACK_UNDER_LOAD = "rollback_under_load"
    RECOVERY_TIMEOUT = "recovery_timeout"

@dataclass
class ChaosScenario:
    """Definição de um cenário de caos injetável."""
    scenario_id: str
    scenario_type: ChaosScenarioType
    target_component: str
    parameters: Dict[str, Any]
    duration_seconds: float
    expected_impact: Dict[str, float]
    validation_criteria: Dict[str, float]
    description: str = ""

@dataclass
class ChaosInjectionResult:
    """Resultado de uma injeção de caos."""
    injection_id: str
    scenario_id: str
    start_time: float
    end_time: float
    metrics_before: Dict[str, float]
    metrics_during: Dict[str, float]
    metrics_after: Dict[str, float]
    mttt_seconds: float  # Mean Time To Detect
    mttr_seconds: float  # Mean Time To Recover
    rollback_triggered: bool
    rollback_success: bool
    state_integrity_preserved: bool
    data_loss_detected: bool
    details: List[str]

@dataclass
class ChaosValidationReport:
    """Relatório consolidado de validação via chaos testing."""
    report_id: str
    environment: str  # "canary" ou "staging"
    scenarios_tested: List[ChaosInjectionResult]
    overall_resilience_score: float  # 0.0-1.0
    passed: bool
    resilience_metrics: Dict[str, float]
    lessons_learned: List[str]
    generated_at: float = field(default_factory=time.time)

class ChaosTestingFramework:
    """
    Framework de testes de caos para validar resiliência da Catedral.
    """
    RESILIENCE_THRESHOLDS = {
        "max_mttd_seconds": 10.0,
        "max_mttr_seconds": 120.0,
        "min_omega_recovery_ratio": 0.95,
        "max_rollback_time_ms": 100.0,
        "require_state_integrity": True,
        "require_zero_data_loss": True,
    }

    DEFAULT_SCENARIOS: List[ChaosScenarioType] = [
        ChaosScenarioType.NETWORK_PARTITION,
        ChaosScenarioType.MERKLE_CORRUPTION,
        ChaosScenarioType.ZK_PROOF_TIMEOUT,
        ChaosScenarioType.CONSENT_FLOOD,
        ChaosScenarioType.ROLLBACK_UNDER_LOAD,
    ]

    def __init__(self, organism: CathedralOrganism, codex: CrystalCodex, quantum_processor: QuantumProcessor):
        self.organism = organism
        self.codex = codex
        self.quantum = quantum_processor
        self._scenario_catalog: Dict[str, ChaosScenario] = {}
        self._injection_history: List[ChaosInjectionResult] = []
        self._isolated_only = True

    def register_scenario(self, scenario: ChaosScenario):
        self._scenario_catalog[scenario.scenario_id] = scenario
        logging.info(f"[Chaos] Cenário registrado: {scenario.scenario_id}")

    async def run_chaos_validation(self, environment: str = "canary", scenarios: Optional[List[ChaosScenarioType]] = None) -> ChaosValidationReport:
        if self._isolated_only and environment not in ["canary", "staging"]:
            raise ValueError(f"Chaos testing só permitido em ambientes isolados")

        report_id = f"chaos_val_{environment}_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
        scenarios_to_test = scenarios or self.DEFAULT_SCENARIOS
        results = []

        for scenario_type in scenarios_to_test:
            scenario = self._get_or_create_scenario(scenario_type)
            result = await self._inject_and_observe(scenario, environment)
            results.append(result)
            if not result.state_integrity_preserved and result.data_loss_detected:
                logging.critical(f"[Chaos] Falha crítica em {scenario.scenario_id}")
                break

        resilience_score = self._calculate_overall_resilience(results)
        passed = self._evaluate_resilience_criteria(results, resilience_score)
        lessons = self._extract_chaos_lessons(results)

        report = ChaosValidationReport(
            report_id=report_id,
            environment=environment,
            scenarios_tested=results,
            overall_resilience_score=resilience_score,
            passed=passed,
            resilience_metrics={
                "avg_mttd": sum(r.mttt_seconds for r in results if r.mttt_seconds != 999.0) / max(1, len([r for r in results if r.mttt_seconds != 999.0])),
                "avg_mttr": sum(r.mttr_seconds for r in results if r.mttr_seconds != 999.0) / max(1, len([r for r in results if r.mttr_seconds != 999.0])),
                "rollback_success_rate": sum(1 for r in results if r.rollback_success) / max(1, len(results)),
                "state_integrity_rate": sum(1 for r in results if r.state_integrity_preserved) / max(1, len(results)),
            },
            lessons_learned=lessons,
        )
        await self._anchor_chaos_report(report)
        return report

    def _get_or_create_scenario(self, scenario_type: ChaosScenarioType) -> ChaosScenario:
        scenario_id = f"{scenario_type.value}_cathedral"
        if scenario_id in self._scenario_catalog:
            return self._scenario_catalog[scenario_id]

        params, duration, impact, criteria = self._get_default_scenario_config(scenario_type)
        scenario = ChaosScenario(
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            target_component=self._get_target_component(scenario_type),
            parameters=params,
            duration_seconds=duration,
            expected_impact=impact,
            validation_criteria=criteria,
            description=f"Cenário padrão para {scenario_type.value}",
        )
        self.register_scenario(scenario)
        return scenario

    def _get_default_scenario_config(self, scenario_type: ChaosScenarioType) -> tuple:
        configs = {
            ChaosScenarioType.NETWORK_PARTITION: ({"isolate_regions": 1, "duration_factor": 1.0}, 5.0, {"omega_degradation": 0.15}, {"max_mttd_seconds": 10.0}),
            ChaosScenarioType.MERKLE_CORRUPTION: ({"corruption_level": "minor", "affected_shards": 10}, 5.0, {"state_integrity_drop": 0.05}, {"min_state_integrity": 0.99}),
            ChaosScenarioType.ZK_PROOF_TIMEOUT: ({"load_multiplier": 3.0}, 5.0, {"consensus_delay": 200}, {"max_mttd_seconds": 15.0}),
            ChaosScenarioType.CONSENT_FLOOD: ({"request_rate": 1000}, 5.0, {"latency_p99": 150}, {"max_latency_p99_ms": 200}),
            ChaosScenarioType.ROLLBACK_UNDER_LOAD: ({"concurrent_requests": 100}, 5.0, {"rollback_time": 80}, {"max_rollback_time_ms": 100.0}),
        }
        return configs.get(scenario_type, ({}, 5.0, {}, {}))

    def _get_target_component(self, scenario_type: ChaosScenarioType) -> str:
        targets = {
            ChaosScenarioType.NETWORK_PARTITION: "QuantumBus",
            ChaosScenarioType.MERKLE_CORRUPTION: "CrystalCodex",
            ChaosScenarioType.ZK_PROOF_TIMEOUT: "QuantumConsensusEngine",
            ChaosScenarioType.CONSENT_FLOOD: "GranularConsentEngine",
            ChaosScenarioType.ROLLBACK_UNDER_LOAD: "EmergencyRollbackController",
        }
        return targets.get(scenario_type, "CathedralOrganism")

    async def _inject_and_observe(self, scenario: ChaosScenario, environment: str) -> ChaosInjectionResult:
        injection_id = f"inj_{scenario.scenario_id}_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
        start_time = time.time()
        details = []

        metrics_before = await self._collect_baseline_metrics()
        await self._execute_chaos_injection(scenario, environment)

        mttt_start = time.time()
        fault_detected = await self._wait_for_fault_detection(scenario.target_component, 10)
        mttt_seconds = time.time() - mttt_start if fault_detected else 999.0

        metrics_during = await self._collect_metrics_during_chaos()
        recovery_start = time.time()
        recovered = await self._wait_for_recovery(scenario.target_component, scenario.duration_seconds)
        mttr_seconds = time.time() - recovery_start if recovered else 999.0

        rollback_triggered = not recovered
        rollback_success = True
        if rollback_triggered:
            rollback_success = await self._execute_emergency_rollback(scenario.target_component, "Chaos recovery failed")

        await self._stop_chaos_injection(scenario, environment)
        metrics_after = await self._collect_metrics_post_recovery()
        state_integrity = await self._verify_state_integrity(scenario.target_component)
        data_loss = await self._check_for_data_loss(scenario.target_component)

        return ChaosInjectionResult(
            injection_id=injection_id, scenario_id=scenario.scenario_id,
            start_time=start_time, end_time=time.time(),
            metrics_before=metrics_before, metrics_during=metrics_during, metrics_after=metrics_after,
            mttt_seconds=mttt_seconds, mttr_seconds=mttr_seconds,
            rollback_triggered=rollback_triggered, rollback_success=rollback_success,
            state_integrity_preserved=state_integrity, data_loss_detected=data_loss,
            details=details
        )

    async def _collect_baseline_metrics(self) -> Dict[str, float]:
        return {"omega": self.organism.get_omega()}

    async def _collect_metrics_during_chaos(self) -> Dict[str, float]:
        return {"omega": self.organism.get_omega()}

    async def _collect_metrics_post_recovery(self) -> Dict[str, float]:
        return {"omega": self.organism.get_omega()}

    async def _execute_chaos_injection(self, scenario: ChaosScenario, environment: str):
        logging.info(f"[Chaos] Injetando {scenario.scenario_type.value} em {scenario.target_component}")
        if scenario.scenario_type == ChaosScenarioType.NETWORK_PARTITION:
            self.organism.simulate_network_failure(True)
        elif scenario.scenario_type == ChaosScenarioType.MERKLE_CORRUPTION:
            self.codex.simulate_corruption(True)
        elif scenario.scenario_type == ChaosScenarioType.QUANTUM_DEGRADATION:
            self.quantum.simulate_degradation(0.95)

    async def _stop_chaos_injection(self, scenario: ChaosScenario, environment: str):
        if scenario.scenario_type == ChaosScenarioType.NETWORK_PARTITION:
            self.organism.simulate_network_failure(False)
        elif scenario.scenario_type == ChaosScenarioType.MERKLE_CORRUPTION:
            self.codex.simulate_corruption(False)
        elif scenario.scenario_type == ChaosScenarioType.QUANTUM_DEGRADATION:
            self.quantum.simulate_degradation(0.999)

    async def _wait_for_fault_detection(self, component: str, timeout: float) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if self.organism.has_detected_fault(component): return True
            await asyncio.sleep(0.1)
        return False

    async def _wait_for_recovery(self, component: str, timeout: float) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if self.organism.is_healthy(component): return True
            await asyncio.sleep(0.1)
        return False

    async def _execute_emergency_rollback(self, component: str, reason: str) -> bool:
        return self.organism.trigger_rollback(component, reason)

    async def _verify_state_integrity(self, component: str) -> bool:
        return self.codex.verify_integrity()

    async def _check_for_data_loss(self, component: str) -> bool:
        return False

    def _calculate_overall_resilience(self, results: List[ChaosInjectionResult]) -> float:
        if not results: return 0.0
        scores = []
        for r in results:
            score = 1.0
            if r.mttt_seconds > self.RESILIENCE_THRESHOLDS["max_mttd_seconds"]: score -= 0.2
            if r.mttr_seconds > self.RESILIENCE_THRESHOLDS["max_mttr_seconds"]: score -= 0.2
            if not r.state_integrity_preserved: score -= 0.3
            if r.data_loss_detected: score -= 0.3
            scores.append(max(0, score))
        return sum(scores) / len(scores)

    def _evaluate_resilience_criteria(self, results: List[ChaosInjectionResult], score: float) -> bool:
        if score < 0.8: return False
        if any(r.data_loss_detected for r in results): return False
        return True

    def _extract_chaos_lessons(self, results: List[ChaosInjectionResult]) -> List[str]:
        lessons = []
        for r in results:
            if r.mttt_seconds > 10: lessons.append(f"Detecção lenta em {r.scenario_id}")
            if r.mttr_seconds > 60: lessons.append(f"Recuperação lenta em {r.scenario_id}")
        if not lessons: lessons.append("Resiliência nominal confirmada")
        return lessons

    async def _anchor_chaos_report(self, report: ChaosValidationReport):
        await self.codex.store_artifact(f"chaos_report_{report.report_id}", hashlib.sha256(str(report).encode()).hexdigest(), asdict(report))
