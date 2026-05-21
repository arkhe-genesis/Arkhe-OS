#!/usr/bin/env python3
"""
ARKHE OS Substrato 398-SOAR — Conector de Orquestração Automática
Integra detecções de partículas com sistemas SOAR para resposta a eventos críticos.
Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
"""

import json
import time
import hashlib
import asyncio
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable
from enum import Enum


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ResponseAction(Enum):
    LOG = "log"
    ALERT = "alert"
    TRIGGER_EXTERNAL = "trigger_external"
    SHUTDOWN = "shutdown"
    ISOLATE = "isolate"


@dataclass
class ParticleEvent:
    timestamp_ns: int
    particle_type: str
    energy_kev: float
    confidence: float
    source_substrate: str
    detector_id: str
    raw_amplitude_mV: float


@dataclass
class SOARDecision:
    event_id: str
    severity: str
    action: str
    reason: str
    agent_consensus: float
    timestamp: float
    seal: str


class ArkheSOARConnector:
    """
    Conector SOAR constitucional para ARKHE OS.

    Regras de resposta:
    - alpha > 5 MeV com confiança > 95%: ALERT + TRIGGER_EXTERNAL
    - muon shower coincidente > 10 nodos: ALERT
    - gamma anômalo (energia não calibrada): INVESTIGATE
    - taxa de eventos > 100x baseline: EMERGENCY / SHUTDOWN
    """

    THRESHOLDS = {
        "alpha_energy_MeV": 5.0,
        "muon_coincidence_nodes": 10,
        "gamma_anomaly_sigma": 3.0,
        "rate_multiplier": 100.0,
        "confidence_min": 0.95
    }

    def __init__(self, callback_url: Optional[str] = None):
        self.callback_url = callback_url
        self.event_history: List[ParticleEvent] = []
        self.decisions: List[SOARDecision] = []
        self.baseline_rate_hz = 1.0
        self.last_rate_check = time.time()
        self.action_handlers: Dict[str, Callable] = {
            "log": self._handle_log,
            "alert": self._handle_alert,
            "trigger_external": self._handle_trigger,
            "shutdown": self._handle_shutdown,
            "isolate": self._handle_isolate
        }

    def _generate_event_id(self, event: ParticleEvent) -> str:
        payload = f"{event.timestamp_ns}|{event.particle_type}|{event.energy_kev:.2f}|{event.detector_id}"
        return hashlib.sha3_256(payload.encode()).hexdigest()[:16]

    def _compute_rate(self) -> float:
        now = time.time()
        window = 10.0  # segundos
        recent = [e for e in self.event_history if (now - e.timestamp_ns / 1e9) < window]
        return len(recent) / window if window > 0 else 0.0

    def evaluate_event(self, event: ParticleEvent, mesh_context: Optional[Dict] = None) -> SOARDecision:
        """Avalia evento e determina resposta SOAR."""
        self.event_history.append(event)
        event_id = self._generate_event_id(event)

        actions = []
        reasons = []
        severity = AlertSeverity.INFO

        # Regra 1: Alpha de alta energia
        if event.particle_type == "alpha" and event.energy_kev > 5000 and event.confidence > self.THRESHOLDS["confidence_min"]:
            severity = AlertSeverity.CRITICAL
            actions.extend([ResponseAction.ALERT.value, ResponseAction.TRIGGER_EXTERNAL.value])
            reasons.append(f"Alpha {event.energy_kev:.1f} keV detected with {event.confidence:.1%} confidence")

        # Regra 2: Muon shower
        if event.particle_type == "muon" and mesh_context:
            coincident_nodes = mesh_context.get("coincident_nodes", 0)
            if coincident_nodes >= self.THRESHOLDS["muon_coincidence_nodes"]:
                severity = AlertSeverity.WARNING if severity == AlertSeverity.INFO else severity
                actions.append(ResponseAction.ALERT.value)
                reasons.append(f"Muon shower detected across {coincident_nodes} nodes")

        # Regra 3: Taxa anômala
        current_rate = self._compute_rate()
        if current_rate > self.baseline_rate_hz * self.THRESHOLDS["rate_multiplier"]:
            severity = AlertSeverity.EMERGENCY
            actions.insert(0, ResponseAction.SHUTDOWN.value)
            reasons.append(f"Event rate {current_rate:.1f} Hz exceeds baseline by {self.THRESHOLDS['rate_multiplier']}x")

        # Regra 4: Gamma anômalo (energia fora da calibração conhecida)
        if event.particle_type == "gamma":
            known_peaks = [662, 1173, 1332]  # Cs-137, Co-60
            closest = min(known_peaks, key=lambda p: abs(p - event.energy_kev))
            if abs(event.energy_kev - closest) > 50 and event.confidence > 0.9:
                severity = max(severity, AlertSeverity.WARNING, key=lambda s: list(AlertSeverity).index(s))
                actions.append(ResponseAction.ALERT.value)
                reasons.append(f"Anomalous gamma energy: {event.energy_kev:.1f} keV (closest known: {closest} keV)")

        # Deduplicar ações
        unique_actions = list(dict.fromkeys(actions))
        if not unique_actions:
            unique_actions = [ResponseAction.LOG.value]
            reasons.append("No critical conditions met")

        # Consenso simulado (em produção: consultar AGI agents)
        consensus = event.confidence * (0.8 + 0.2 * len(unique_actions))

        decision = SOARDecision(
            event_id=event_id,
            severity=severity.value,
            action=",".join(unique_actions),
            reason="; ".join(reasons),
            agent_consensus=round(min(1.0, consensus), 4),
            timestamp=time.time(),
            seal=""
        )

        # Gerar selo
        seal_payload = json.dumps(asdict(decision), sort_keys=True)
        decision.seal = hashlib.sha3_256(seal_payload.encode()).hexdigest()[:32]

        self.decisions.append(decision)
        self._execute_actions(decision, event)
        return decision

    def _execute_actions(self, decision: SOARDecision, event: ParticleEvent):
        """Executa ações determinadas."""
        for action in decision.action.split(","):
            handler = self.action_handlers.get(action)
            if handler:
                handler(decision, event)

    def _handle_log(self, decision: SOARDecision, event: ParticleEvent):
        print(f"[SOAR-LOG] {decision.event_id}: {decision.reason}")

    def _handle_alert(self, decision: SOARDecision, event: ParticleEvent):
        alert_payload = {
            "event_id": decision.event_id,
            "severity": decision.severity,
            "reason": decision.reason,
            "detector": event.detector_id,
            "energy_kev": event.energy_kev,
            "timestamp": decision.timestamp,
            "seal": decision.seal
        }
        print(f"[SOAR-ALERT] {json.dumps(alert_payload, indent=2)}")
        # Em produção: enviar para FEMA IPAWS, CENAD, ou webhook

    def _handle_trigger(self, decision: SOARDecision, event: ParticleEvent):
        print(f"[SOAR-TRIGGER] External system triggered for {decision.event_id}")
        # Em produção: acionar sirene, fechar shutters, notificar equipe

    def _handle_shutdown(self, decision: SOARDecision, event: ParticleEvent):
        print(f"[SOAR-SHUTDOWN] EMERGENCY shutdown initiated: {decision.reason}")
        # Em produção: desligar HV, fechar válvulas, salvar estado

    def _handle_isolate(self, decision: SOARDecision, event: ParticleEvent):
        print(f"[SOAR-ISOLATE] Isolating detector {event.detector_id}")

    def get_statistics(self) -> Dict:
        """Estatísticas de decisões SOAR."""
        if not self.decisions:
            return {}
        severity_counts = {}
        for d in self.decisions:
            severity_counts[d.severity] = severity_counts.get(d.severity, 0) + 1
        return {
            "total_events_processed": len(self.event_history),
            "total_decisions": len(self.decisions),
            "severity_distribution": severity_counts,
            "average_consensus": sum(d.agent_consensus for d in self.decisions) / len(self.decisions),
            "last_decision": asdict(self.decisions[-1]) if self.decisions else {}
        }


def main():
    print("=" * 70)
    print("ARKHE OS — SOAR CONNECTOR (Substrato 398-SOAR)")
    print("=" * 70)

    soar = ArkheSOARConnector()

    # Simular eventos
    test_events = [
        ParticleEvent(1_000_000_000, "alpha", 5486, 0.97, "390-OPT", "DET-001", 1650.0),
        ParticleEvent(1_000_001_000, "muon", 4000, 0.92, "397-MESH", "DET-042", 600.0),
        ParticleEvent(1_000_002_000, "gamma", 850, 0.91, "390-OPT", "DET-003", 120.0),
        ParticleEvent(1_000_003_000, "alpha", 1200, 0.88, "390-OPT", "DET-001", 350.0),
    ]

    for event in test_events:
        mesh_ctx = {"coincident_nodes": 12} if event.particle_type == "muon" else None
        decision = soar.evaluate_event(event, mesh_ctx)
        print(f"\nEvento {decision.event_id}:")
        print(f"   Severidade: {decision.severity}")
        print(f"   Ação: {decision.action}")
        print(f"   Razão: {decision.reason}")
        print(f"   Consenso: {decision.agent_consensus}")
        print(f"   Selo: {decision.seal}")

    print("\n" + "=" * 70)
    print("ESTATÍSTICAS SOAR")
    print("=" * 70)
    stats = soar.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    main()