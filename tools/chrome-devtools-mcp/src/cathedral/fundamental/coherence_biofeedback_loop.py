#!/usr/bin/env python3
"""
coherence_biofeedback_loop.py
==========================================================
Subprojeto Arcano #41 — Fase 4: Loop de Biofeedback de Coerência

Conecta a interface Ω-TDA (Módulo B) à rede integrada, permitindo
modulação em tempo real do atrator Ω baseada em padrões de spikes
e eventos OR.

Implementa controle PID fotônico para manter Ω no setpoint alvo
(Ω = 0.971 ± δ), com salvaguardas éticas e auditoria contínua.

Arkhe(n) Framework v3.0 — Catedral Arkhe, 2026.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
import hashlib
import time
from enum import Enum

class BiofeedbackMode(Enum):
    """Modos de operação do loop de biofeedback."""
    PASSIVE_MONITORING = "passive_monitoring"  # Apenas mede, não modula
    ACTIVE_STABILIZATION = "active_stabilization"  # Mantém Ω no setpoint
    CONSCIOUSNESS_AMPLIFICATION = "consciousness_amplification"  # Amplifica estados conscientes
    ETHICAL_INTERVENTION = "ethical_intervention"  # Intervém apenas com consentimento explícito

@dataclass
class EthicalGuardrails:
    """Salvaguardas éticas para modulação de estados conscientes."""
    informed_consent_required: bool = True
    max_omega_deviation: float = 0.05  # ΔΩ máximo permitido: 0.971 ± 0.05
    max_intervention_duration_s: float = 300.0  # 5 minutos máximo por sessão
    min_coherence_threshold: float = 0.80  # Não intervir se coerência basal < 0.80
    audit_log_enabled: bool = True
    emergency_stop_enabled: bool = True

    def check_intervention_allowed(self, current_omega: float,
                                baseline_coherence: float,
                                consent_status: bool,
                                session_duration_s: float) -> Dict[str, any]:
        """Verifica se intervenção é permitida dadas as salvaguardas éticas."""
        violations = []

        if self.informed_consent_required and not consent_status:
            violations.append("informed_consent_missing")

        if abs(current_omega - 0.971) > self.max_omega_deviation:
            violations.append("omega_deviation_exceeded")

        if baseline_coherence < self.min_coherence_threshold:
            violations.append("baseline_coherence_too_low")

        if session_duration_s > self.max_intervention_duration_s:
            violations.append("session_duration_exceeded")

        return {
            "allowed": len(violations) == 0,
            "violations": violations,
            "recommendation": "proceed" if len(violations) == 0 else "abort_intervention"
        }

@dataclass
class PIDPhotonicController:
    """Controlador PID fotônico para modulação de Ω via nano-LEDs."""
    kp: float = 0.4  # Ganho proporcional
    ki: float = 0.15  # Ganho integral
    kd: float = 0.05  # Ganho derivativo
    setpoint: float = 0.971  # Ω alvo
    output_min: float = -1.0  # Intensidade mínima dos LEDs (anestesia simulada)
    output_max: float = 1.0  # Intensidade máxima (amplificação de coerência)

    # Estado interno
    integral: float = 0.0
    last_error: float = 0.0
    last_output: float = 0.0
    dt: float = 0.001  # 1 ms, resolução temporal do controle

    def compute(self, measured_omega: float, consent_status: bool,
               ethical_guardrails: EthicalGuardrails,
               session_duration_s: float) -> Dict[str, any]:
        """
        Computa ação de controle com verificação ética integrada.

        Retorna dicionário com:
        - led_intensity: sinal para nano-LEDs (-1.0 a 1.0)
        - ethical_status: resultado da verificação ética
        - audit_entry: registro para auditoria
        """
        # 1. Verificar salvaguardas éticas antes de qualquer ação
        ethical_check = ethical_guardrails.check_intervention_allowed(
            current_omega=measured_omega,
            baseline_coherence=0.92,  # Simulado: coerência basal do usuário
            consent_status=consent_status,
            session_duration_s=session_duration_s
        )

        if not ethical_check["allowed"]:
            # Intervenção não permitida: retornar ação neutra
            return {
                "led_intensity": 0.0,
                "ethical_status": ethical_check,
                "audit_entry": {
                    "timestamp_ns": time.time_ns(),
                    "action": "intervention_blocked",
                    "reason": ethical_check["violations"],
                    "measured_omega": measured_omega
                },
                "control_mode": "ethical_override"
            }

        # 2. Calcular erro e ação PID (apenas se ética permitir)
        error = self.setpoint - measured_omega
        self.integral += error * self.dt
        derivative = (error - self.last_error) / self.dt

        output = (self.kp * error +
                 self.ki * self.integral +
                 self.kd * derivative)

        # Limitar output e aplicar anti-windup
        output = np.clip(output, self.output_min, self.output_max)
        if output != self.last_output:
            # Anti-windup: congelar integral se output saturado
            if output == self.output_min or output == self.output_max:
                self.integral -= error * self.dt

        self.last_error = error
        self.last_output = output

        # 3. Gerar entrada de auditoria
        audit_entry = {
            "timestamp_ns": time.time_ns(),
            "action": "led_intensity_adjusted",
            "measured_omega": measured_omega,
            "target_omega": self.setpoint,
            "led_intensity": float(output),
            "error": float(error),
            "integral": float(self.integral),
            "derivative": float(derivative),
            "ethical_check_passed": True
        }

        return {
            "led_intensity": float(output),
            "ethical_status": ethical_check,
            "audit_entry": audit_entry,
            "control_mode": "pid_active"
        }

    def reset(self):
        """Reseta estado interno do controlador."""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_output = 0.0

@dataclass
class CoherenceBiofeedbackLoop:
    """Loop completo de biofeedback de coerência."""
    pid_controller: PIDPhotonicController
    ethical_guardrails: EthicalGuardrails
    mode: BiofeedbackMode = BiofeedbackMode.ACTIVE_STABILIZATION

    # Estado da sessão
    session_start_ns: Optional[int] = None
    consent_status: bool = False
    audit_log: List[Dict] = field(default_factory=list)

    # Callbacks para integração com sistema maior
    omega_measurement_callback: Optional[Callable[[], float]] = None
    led_actuation_callback: Optional[Callable[[float], bool]] = None
    audit_logging_callback: Optional[Callable[[Dict], None]] = None

    def start_session(self, consent_status: bool) -> Dict[str, any]:
        """Inicia nova sessão de biofeedback com consentimento explícito."""
        self.session_start_ns = time.time_ns()
        self.consent_status = consent_status
        self.pid_controller.reset()
        self.audit_log = []

        start_entry = {
            "event": "session_started",
            "timestamp_ns": self.session_start_ns,
            "consent_status": consent_status,
            "mode": self.mode.value,
            "ethical_guardrails": {
                "max_omega_deviation": self.ethical_guardrails.max_omega_deviation,
                "max_duration_s": self.ethical_guardrails.max_intervention_duration_s
            }
        }
        self._log_audit(start_entry)

        return {
            "session_id": hashlib.sha256(f"{self.session_start_ns}".encode()).hexdigest()[:16],
            "status": "active",
            "message": "Biofeedback session started. Monitoring coherence..."
        }

    def step(self, measured_omega: Optional[float] = None) -> Dict[str, any]:
        """
        Executa um passo do loop de biofeedback.

        Se measured_omega não for fornecido, tenta obter via callback.
        """
        if self.session_start_ns is None:
            return {"error": "session_not_started", "action_required": "call start_session()"}

        # Obter medida de Ω (via callback ou argumento)
        if measured_omega is None and self.omega_measurement_callback:
            measured_omega = self.omega_measurement_callback()
        elif measured_omega is None:
            return {"error": "omega_measurement_missing", "action_required": "provide measured_omega or set callback"}

        # Calcular duração da sessão
        session_duration_s = (time.time_ns() - self.session_start_ns) / 1e9

        # Computar ação de controle (com verificação ética integrada)
        control_result = self.pid_controller.compute(
            measured_omega=measured_omega,
            consent_status=self.consent_status,
            ethical_guardrails=self.ethical_guardrails,
            session_duration_s=session_duration_s
        )

        # Atuar nos nano-LEDs se permitido e callback disponível
        if control_result["led_intensity"] != 0.0 and self.led_actuation_callback:
            success = self.led_actuation_callback(control_result["led_intensity"])
            control_result["actuation_success"] = success

        # Registrar entrada de auditoria
        self._log_audit(control_result["audit_entry"])

        # Verificar condições de término da sessão
        if session_duration_s > self.ethical_guardrails.max_intervention_duration_s:
            return self._end_session("duration_exceeded")
        if self.ethical_guardrails.emergency_stop_enabled and self._check_emergency_stop():
            return self._end_session("emergency_stop_triggered")

        return {
            "status": "running",
            "measured_omega": measured_omega,
            "target_omega": self.pid_controller.setpoint,
            "led_intensity": control_result["led_intensity"],
            "ethical_status": control_result["ethical_status"],
            "session_duration_s": session_duration_s,
            "control_mode": control_result["control_mode"]
        }

    def end_session(self, reason: str = "user_requested") -> Dict[str, any]:
        """Encerra sessão de biofeedback de forma controlada."""
        return self._end_session(reason)

    def _end_session(self, reason: str) -> Dict[str, any]:
        """Implementação interna de término de sessão."""
        end_entry = {
            "event": "session_ended",
            "timestamp_ns": time.time_ns(),
            "reason": reason,
            "total_duration_s": (time.time_ns() - self.session_start_ns) / 1e9 if self.session_start_ns else 0,
            "total_audit_entries": len(self.audit_log)
        }
        self._log_audit(end_entry)

        # Resetar estado
        self.session_start_ns = None
        self.consent_status = False
        self.pid_controller.reset()

        return {
            "status": "ended",
            "reason": reason,
            "audit_log_summary": {
                "total_entries": len(self.audit_log),
                "interventions_blocked": sum(1 for e in self.audit_log if e.get("action") == "intervention_blocked"),
                "interventions_applied": sum(1 for e in self.audit_log if e.get("action") == "led_intensity_adjusted")
            },
            "message": f"Biofeedback session ended: {reason}"
        }

    def _log_audit(self, entry: Dict):
        """Registra entrada no log de auditoria."""
        self.audit_log.append(entry)
        if self.audit_logging_callback:
            self.audit_logging_callback(entry)

    def _check_emergency_stop(self) -> bool:
        """Verifica condições de parada de emergência (simulado)."""
        # Em produção: monitorar sinais fisiológicos críticos, falhas de hardware, etc.
        # Para simulação: retorno aleatório com baixa probabilidade
        return np.random.random() < 0.001  # 0.1% de chance de emergência por passo
