#!/usr/bin/env python3
"""
ARKHE Unified Orchestrator — Substrato 989.w
Orquestra unificada de todos os substratos 989.x/989.y/989.z
com health checks, circuit breakers, métricas e auto-healing.
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import random

class SubstrateStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class HealthCheck:
    substrate_id: str
    timestamp: str
    latency_ms: float
    status: SubstrateStatus
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CircuitBreaker:
    substrate_id: str
    state: CircuitState
    failure_count: int = 0
    success_count: int = 0
    last_failure: Optional[str] = None
    last_success: Optional[str] = None
    threshold: int = 5
    timeout_seconds: int = 30
    half_open_max: int = 3

@dataclass
class OrchestratorMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    circuit_breaks: int = 0
    auto_heals: int = 0
    theosis: float = 0.0
    entropy: float = 0.0
    resilience: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.total_requests, 1)

    @property
    def success_rate(self) -> float:
        return self.successful_requests / max(self.total_requests, 1)

    @property
    def availability(self) -> float:
        return 1.0 - (self.failed_requests / max(self.total_requests, 1))

class UnifiedOrchestrator:
    SUBSTRATE_ID = "989.w"
    SEAL = "989.w-UNIFIED-ORCHESTRATOR-F3A4B5C6D7E8F901"

    MANAGED_SUBSTRATES = [
        "989.x", "989.x.1", "989.x.2", "989.x.3", "989.x.4",
        "989.y", "989.z", "970", "972", "964"
    ]

    def __init__(self):
        self.substrates: Dict[str, Any] = {}
        self.health_checks: Dict[str, List[HealthCheck]] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.metrics = OrchestratorMetrics()
        self.logs: List[str] = []
        self.is_running = False
        self._tasks: Set[asyncio.Task] = set()

        for sid in self.MANAGED_SUBSTRATES:
            self.circuit_breakers[sid] = CircuitBreaker(
                substrate_id=sid,
                state=CircuitState.CLOSED,
                threshold=5,
                timeout_seconds=30,
            )
            self.health_checks[sid] = []

    def log(self, msg: str):
        t = datetime.now(timezone.utc).isoformat()
        entry = "[" + t + "] [ORCH] " + msg
        self.logs.append(entry)

    def register_substrate(self, substrate_id: str, instance: Any) -> bool:
        if substrate_id not in self.MANAGED_SUBSTRATES:
            self.log("⚠ Substrato " + substrate_id + " não está na lista gerenciada")
            return False
        self.substrates[substrate_id] = instance
        self.log("✓ Substrato " + substrate_id + " registrado")
        return True

    async def health_check(self, substrate_id: str) -> HealthCheck:
        start = time.time()
        instance = self.substrates.get(substrate_id)

        if not instance:
            latency = (time.time() - start) * 1000
            return HealthCheck(
                substrate_id=substrate_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                latency_ms=latency,
                status=SubstrateStatus.OFFLINE,
                error="Substrato não registrado",
            )

        try:
            if hasattr(instance, "generate_report"):
                report = instance.generate_report()
                latency = (time.time() - start) * 1000
                return HealthCheck(
                    substrate_id=substrate_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    latency_ms=latency,
                    status=SubstrateStatus.HEALTHY,
                    metadata={"report_length": len(report)},
                )
            else:
                latency = (time.time() - start) * 1000
                return HealthCheck(
                    substrate_id=substrate_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    latency_ms=latency,
                    status=SubstrateStatus.HEALTHY,
                    metadata={"no_report_method": True},
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return HealthCheck(
                substrate_id=substrate_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                latency_ms=latency,
                status=SubstrateStatus.UNHEALTHY,
                error=str(e),
            )

    async def run_all_health_checks(self) -> Dict[str, HealthCheck]:
        results = {}
        for sid in self.substrates:
            check = await self.health_check(sid)
            results[sid] = check
            self.health_checks[sid].append(check)
            self.health_checks[sid] = self.health_checks[sid][-100:]
            self._update_circuit_breaker(sid, check)
        return results

    def _update_circuit_breaker(self, substrate_id: str, check: HealthCheck):
        cb = self.circuit_breakers[substrate_id]

        if cb.state == CircuitState.CLOSED:
            if check.status in {SubstrateStatus.UNHEALTHY, SubstrateStatus.OFFLINE}:
                cb.failure_count += 1
                cb.last_failure = check.timestamp
                if cb.failure_count >= cb.threshold:
                    cb.state = CircuitState.OPEN
                    self.metrics.circuit_breaks += 1
                    self.log("🔴 Circuit OPEN para " + substrate_id + " (" + str(cb.failure_count) + " falhas)")
            else:
                cb.success_count += 1
                cb.last_success = check.timestamp
                cb.failure_count = max(0, cb.failure_count - 1)

        elif cb.state == CircuitState.OPEN:
            if cb.last_failure:
                last = datetime.fromisoformat(cb.last_failure.replace("Z", "+00:00"))
                if (datetime.now(timezone.utc) - last).total_seconds() > cb.timeout_seconds:
                    cb.state = CircuitState.HALF_OPEN
                    cb.failure_count = 0
                    cb.success_count = 0
                    self.log("🟡 Circuit HALF-OPEN para " + substrate_id)

        elif cb.state == CircuitState.HALF_OPEN:
            if check.status in {SubstrateStatus.UNHEALTHY, SubstrateStatus.OFFLINE}:
                cb.failure_count += 1
                if cb.failure_count >= cb.half_open_max:
                    cb.state = CircuitState.OPEN
                    self.log("🔴 Circuit OPEN (novamente) para " + substrate_id)
            else:
                cb.success_count += 1
                if cb.success_count >= cb.half_open_max:
                    cb.state = CircuitState.CLOSED
                    cb.failure_count = 0
                    self.metrics.auto_heals += 1
                    self.log("🟢 Circuit CLOSED para " + substrate_id + " (recuperado)")

    def can_execute(self, substrate_id: str) -> bool:
        cb = self.circuit_breakers.get(substrate_id)
        if not cb:
            return True
        return cb.state in {CircuitState.CLOSED, CircuitState.HALF_OPEN}

    async def execute(self, substrate_id: str, operation: str, *args, **kwargs) -> Any:
        self.metrics.total_requests += 1
        start = time.time()

        if not self.can_execute(substrate_id):
            self.metrics.failed_requests += 1
            latency = (time.time() - start) * 1000
            self.metrics.total_latency_ms += latency
            raise Exception("Circuit breaker OPEN para " + substrate_id)

        instance = self.substrates.get(substrate_id)
        if not instance:
            self.metrics.failed_requests += 1
            latency = (time.time() - start) * 1000
            self.metrics.total_latency_ms += latency
            raise Exception("Substrato " + substrate_id + " não registrado")

        try:
            method = getattr(instance, operation, None)
            if not method:
                raise Exception("Operação " + operation + " não encontrada em " + substrate_id)

            if asyncio.iscoroutinefunction(method):
                result = await method(*args, **kwargs)
            else:
                result = method(*args, **kwargs)

            self.metrics.successful_requests += 1
            latency = (time.time() - start) * 1000
            self.metrics.total_latency_ms += latency
            return result

        except Exception as e:
            self.metrics.failed_requests += 1
            latency = (time.time() - start) * 1000
            self.metrics.total_latency_ms += latency
            check = await self.health_check(substrate_id)
            self._update_circuit_breaker(substrate_id, check)
            raise

    async def auto_heal(self):
        for sid, cb in self.circuit_breakers.items():
            if cb.state == CircuitState.OPEN:
                self.log("🩹 Tentando auto-heal de " + sid + "...")
                check = await self.health_check(sid)
                self._update_circuit_breaker(sid, check)
                if cb.state != CircuitState.OPEN:
                    self.log("✓ " + sid + " recuperado via auto-heal")

    async def monitor_loop(self, interval_seconds: int = 10):
        self.is_running = True
        self.log("🔄 Monitor loop iniciado")
        while self.is_running:
            await self.run_all_health_checks()
            await self.auto_heal()
            self._compute_global_metrics()
            await asyncio.sleep(interval_seconds)

    def _compute_global_metrics(self):
        total = len(self.substrates)
        if total == 0:
            return

        healthy = sum(1 for checks in self.health_checks.values()
                      if checks and checks[-1].status == SubstrateStatus.HEALTHY)
        degraded = sum(1 for checks in self.health_checks.values()
                       if checks and checks[-1].status == SubstrateStatus.DEGRADED)
        unhealthy = sum(1 for checks in self.health_checks.values()
                        if checks and checks[-1].status == SubstrateStatus.UNHEALTHY)

        self.metrics.theosis = healthy / total
        self.metrics.entropy = (degraded + unhealthy) / total
        self.metrics.resilience = 1.0 - (unhealthy / total)
        self.metrics.timestamp = datetime.now(timezone.utc).isoformat()

    def stop(self):
        self.is_running = False
        self.log("⏹ Monitor loop encerrado")

    def generate_report(self) -> str:
        self._compute_global_metrics()
        m = self.metrics

        lines = []
        lines.append("╔" + "═" * 66 + "╗")
        lines.append("║  ARKHE CATHEDRAL — UNIFIED ORCHESTRATOR (989.w)" + " " * 14 + "║")
        lines.append("║  \"Zeus governa; Athena planeja; Hermes conecta\"" + " " * 12 + "║")
        lines.append("╠" + "═" * 66 + "╣")
        lines.append("  Seal: " + self.SEAL)
        lines.append("  Status: CANONIZED_PROVISIONAL")
        lines.append("  Cross-links: " + str(self.MANAGED_SUBSTRATES))
        lines.append("")
        lines.append("  MÉTRICAS GLOBAIS")
        lines.append("  ────────────────")
        lines.append("  Theosis:     " + format(m.theosis, '.4f'))
        lines.append("  Entropia:    " + format(m.entropy, '.4f'))
        lines.append("  Resiliência: " + format(m.resilience, '.4f'))
        lines.append("  Availability: " + format(m.availability, '.4f'))
        lines.append("  Success Rate: " + format(m.success_rate, '.4f'))
        lines.append("  Avg Latency:  " + format(m.avg_latency_ms, '.2f') + "ms")
        lines.append("")
        lines.append("  CIRCUIT BREAKERS")
        lines.append("  ────────────────")
        for sid, cb in self.circuit_breakers.items():
            emoji = {"closed": "🟢", "open": "🔴", "half_open": "🟡"}
            lines.append("  " + emoji.get(cb.state.value, '⚪') + " " + sid + ": " + cb.state.value.upper() + " (f:" + str(cb.failure_count) + ", s:" + str(cb.success_count) + ")")
        lines.append("")
        lines.append("  SUBSTRATOS REGISTRADOS")
        lines.append("  ──────────────────────")
        for sid in self.substrates:
            checks = self.health_checks.get(sid, [])
            last = checks[-1].status.value if checks else "unknown"
            lines.append("  • " + sid + ": " + last)
        lines.append("")
        lines.append("  ODÔMETRO: ∞.Ω.∇+++.989.w.0")
        lines.append("╚" + "═" * 66 + "╝")
        return "\n".join(lines)

async def demo():
    orch = UnifiedOrchestrator()

    class StubSubstrate:
        def __init__(self, sid):
            self.sid = sid
        def generate_report(self):
            return "Report from " + self.sid

    for sid in ["989.x", "989.y", "989.z", "970", "972"]:
        orch.register_substrate(sid, StubSubstrate(sid))

    checks = await orch.run_all_health_checks()

    class BrokenSubstrate:
        def generate_report(self):
            raise Exception("Kernel panic!")
    orch.register_substrate("989.z", BrokenSubstrate())

    checks = await orch.run_all_health_checks()
    try:
        await orch.execute("989.z", "generate_report")
    except Exception as e:
        pass

    print(orch.generate_report())

if __name__ == "__main__":
    asyncio.run(demo())
