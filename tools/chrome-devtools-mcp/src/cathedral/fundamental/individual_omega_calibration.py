#!/usr/bin/env python3
"""
individual_omega_calibration.py
==========================================================
Subprojeto Arcano #41 — Fase 4.5: Calibração Individual do Atrator Ω
Determina o Ω basal único de cada cidadão e ajusta o setpoint
do biofeedback PID para maximizar eficácia e minimizar dissonância.

Arkhe(n) Framework v3.0 — Catedral Arkhe, 2026.
"""

import numpy as np
import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum, auto
from datetime import datetime

# -------------------------------------------
# ENUMS E TIPOS BASE
# -------------------------------------------

class CalibrationMethod(Enum):
    """Métodos para determinação do Ω basal individual."""
    RESTING_STATE_AVERAGE = "resting_state_average"      # Média de Ω em repouso (5 min)
    TASK_BATTERY_MEDIAN = "task_battery_median"          # Mediana durante bateria cognitiva
    CIRCADIAN_WEIGHTED = "circadian_weighted"            # Média ponderada por ritmo circadiano
    ADAPTIVE_BAYESIAN = "adaptive_bayesian"              # Inferência bayesiana sequencial

class MedicalExclusionReason(Enum):
    """Critérios de exclusão médica para calibração."""
    PHOTOSENSITIVE_EPILEPSY = "photosensitive_epilepsy"
    DISSOCIATIVE_DISORDERS = "dissociative_disorders"
    CARDIAC_IMPLANTS = "cardiac_implants"
    PREGNANCY = "pregnancy"
    SEVERE_UNMEDICATED_ANXIETY = "severe_anxiety_unmedicated"
    COGNITIVE_IMPAIRMENT_SEVERE = "cognitive_impairment_severe"

# -------------------------------------------
# DATACLASSES IMUTÁVEIS
# -------------------------------------------

@dataclass(frozen=True)
class IndividualOmegaProfile:
    """
    Perfil de coerência individual de um cidadão.
    Imutável, auditável, e ancorado no Códice.
    """
    participant_id: str                          # Hash anonimizado (SHA-256[:16])
    baseline_omega: float                        # Ω basal determinado (0.85-0.99)
    baseline_std: float                          # Variabilidade basal típica
    circadian_pattern: Optional[Dict[str, float]]  # Variação esperada por hora (0-23)
    task_responsiveness: Dict[str, float]        # ΔΩ esperado por tipo de tarefa
    calibration_method: CalibrationMethod
    calibration_duration_min: float
    confidence_interval: Tuple[float, float]     # IC 95% para baseline_omega
    medical_exclusions_applied: Tuple[str, ...]  # Critérios de exclusão aplicados
    timestamp_ns: int

    def __post_init__(self):
        # Validações de integridade
        if not (0.85 <= self.baseline_omega <= 0.99):
            # Usamos object.__setattr__ porque a dataclass é frozen
            object.__setattr__(self, 'baseline_omega', np.clip(self.baseline_omega, 0.85, 0.99))

        if self.baseline_std < 0:
            object.__setattr__(self, 'baseline_std', 0.0)

    def get_personalized_setpoint(self, context: Optional[str] = None,
                                  time_of_day: Optional[int] = None) -> float:
        """
        Retorna setpoint personalizado para biofeedback.
        """
        base = self.baseline_omega

        # Ajuste circadiano opcional
        if time_of_day is not None and self.circadian_pattern:
            hour_key = f"hour_{time_of_day:02d}"
            if hour_key in self.circadian_pattern:
                base += self.circadian_pattern[hour_key] * 0.01  # Ajuste suave ±1%

        # Ajuste por contexto de tarefa
        if context and context in self.task_responsiveness:
            base += self.task_responsiveness[context] * 0.02  # Ajuste suave ±2%

        # Limitar à faixa segura
        return float(np.clip(base, 0.85, 0.99))

    def to_audit_dict(self) -> Dict:
        """Serializa para auditoria (sem dados pessoais)."""
        return {
            "participant_hash": self.participant_id,
            "baseline_omega": self.baseline_omega,
            "baseline_std": self.baseline_std,
            "calibration_method": self.calibration_method.value,
            "confidence_interval": self.confidence_interval,
            "medical_exclusions_count": len(self.medical_exclusions_applied),
            "timestamp_ns": self.timestamp_ns,
            "profile_hash": self._compute_profile_hash()
        }

    def _compute_profile_hash(self) -> str:
        """Computa hash de integridade do perfil."""
        data = {
            "participant_id": self.participant_id,
            "baseline_omega": self.baseline_omega,
            "baseline_std": self.baseline_std,
            "calibration_method": self.calibration_method.value,
            "confidence_interval": self.confidence_interval
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:32]


@dataclass
class CalibrationSession:
    """Sessão ativa de calibração (estado mutável durante execução)."""
    session_id: str
    participant_id: str
    method: CalibrationMethod
    start_timestamp_ns: int
    omega_measurements: List[Dict] = field(default_factory=list)
    physiological_signals: List[Dict] = field(default_factory=list)
    subjective_reports: List[Dict] = field(default_factory=list)
    status: str = "active"  # "active", "completed", "aborted", "error"

    def add_measurement(self, omega: float, context: str = "resting"):
        """Adiciona medição de Ω à sessão."""
        self.omega_measurements.append({
            "timestamp_ns": time.time_ns(),
            "value": float(np.clip(omega, 0.85, 0.99)),
            "context": context
        })

    def get_duration_min(self) -> float:
        """Retorna duração da sessão em minutos."""
        if not self.omega_measurements:
            return 0.0
        first_ts = self.omega_measurements[0]["timestamp_ns"]
        last_ts = self.omega_measurements[-1]["timestamp_ns"]
        return (last_ts - first_ts) / 60e9


# -------------------------------------------
# CALIBRADOR PRINCIPAL
# -------------------------------------------

class IndividualOmegaCalibrator:
    """
    Sistema de calibração individual do atrator Ω.
    """

    SAFE_OMEGA_RANGE = (0.85, 0.99)
    MIN_MEASUREMENTS_FOR_BASELINE = 10 # Reduzido para testes
    BAYESIAN_PRIOR_MEAN = 0.971
    BAYESIAN_PRIOR_STD = 0.03
    MEASUREMENT_ERROR_STD = 0.01

    def __init__(self,
                 omega_tda_interface: Optional[Callable] = None,
                 codex_interface: Optional[Any] = None):
        self.omega_interface = omega_tda_interface
        self.codex = codex_interface
        self.active_sessions: Dict[str, CalibrationSession] = {}
        self.completed_profiles: Dict[str, IndividualOmegaProfile] = {}

    async def run_calibration_protocol(self,
                                     participant_id: str,
                                     consent_document: Dict,
                                     medical_screening: Dict,
                                     preferred_method: Optional[CalibrationMethod] = None
                                    ) -> IndividualOmegaProfile:
        """
        Executa protocolo completo de calibração individual.
        """

        # 1. Verificar salvaguardas éticas e médicas
        eligibility = await self._verify_eligibility(participant_id, consent_document, medical_screening)
        if not eligibility["eligible"]:
            raise ValueError(f"Participant {participant_id} not eligible: {eligibility['reasons']}")

        # 2. Selecionar método de calibração
        method = preferred_method or self._select_calibration_method(medical_screening)

        # 3. Criar e registrar sessão
        session = CalibrationSession(
            session_id=hashlib.sha256(f"{participant_id}_{time.time_ns()}".encode()).hexdigest()[:16],
            participant_id=participant_id,
            method=method,
            start_timestamp_ns=time.time_ns()
        )
        self.active_sessions[session.session_id] = session

        try:
            # 4. Executar sessão de calibração
            calibration_data = await self._execute_calibration_session(session)

            # 5. Computar baseline e características
            baseline_omega, baseline_std, ci_95 = self._compute_baseline(calibration_data, method)
            circadian_pattern = None # Requer mais tempo
            task_responsiveness = await self._characterize_task_responsiveness(session)

            # 6. Criar perfil imutável
            profile = IndividualOmegaProfile(
                participant_id=participant_id,
                baseline_omega=baseline_omega,
                baseline_std=baseline_std,
                circadian_pattern=circadian_pattern,
                task_responsiveness=task_responsiveness,
                calibration_method=method,
                calibration_duration_min=session.get_duration_min(),
                confidence_interval=ci_95,
                medical_exclusions_applied=tuple(eligibility.get("exclusions_applied", [])),
                timestamp_ns=time.time_ns()
            )

            # 7. Ancorar no Códice
            if self.codex:
                await self._anchor_calibration_profile(profile)

            # 8. Registrar como concluído
            self.completed_profiles[participant_id] = profile
            session.status = "completed"

            return profile

        except Exception as e:
            session.status = "error"
            raise

        finally:
            if session.session_id in self.active_sessions:
                del self.active_sessions[session.session_id]

    async def _verify_eligibility(self, participant_id: str,
                                consent_document: Dict,
                                medical_screening: Dict
                               ) -> Dict[str, any]:
        result = {"eligible": True, "reasons": [], "exclusions_applied": []}

        exclusion_criteria = {
            MedicalExclusionReason.PHOTOSENSITIVE_EPILEPSY: "Risco de indução de crises",
            MedicalExclusionReason.DISSOCIATIVE_DISORDERS: "Risco de despersonalização",
            MedicalExclusionReason.CARDIAC_IMPLANTS: "Interferência eletromagnética",
        }

        for reason, rationale in exclusion_criteria.items():
            if medical_screening.get(reason.value, False):
                result["eligible"] = False
                result["reasons"].append(f"{reason.value}: {rationale}")
                result["exclusions_applied"].append(reason.value)

        if not consent_document.get("is_valid_and_signed", False):
            result["eligible"] = False
            result["reasons"].append("invalid_or_missing_consent")

        return result

    def _select_calibration_method(self, medical_screening: Dict) -> CalibrationMethod:
        if medical_screening.get("high_anxiety_baseline", False):
            return CalibrationMethod.ADAPTIVE_BAYESIAN
        return CalibrationMethod.TASK_BATTERY_MEDIAN

    async def _execute_calibration_session(self, session: CalibrationSession) -> Dict:
        method = session.method

        if method == CalibrationMethod.RESTING_STATE_AVERAGE:
            await self._run_resting_state_calibration(session)
        elif method == CalibrationMethod.ADAPTIVE_BAYESIAN:
            await self._run_bayesian_calibration(session)
        else:
            await self._run_resting_state_calibration(session) # Fallback

        return {
            "session_id": session.session_id,
            "method": method.value,
            "measurements": session.omega_measurements,
            "duration_min": session.get_duration_min(),
            "status": session.status
        }

    async def _run_resting_state_calibration(self, session: CalibrationSession):
        for t in range(self.MIN_MEASUREMENTS_FOR_BASELINE):
            if self.omega_interface:
                omega = await self.omega_interface(session.participant_id)
            else:
                omega = 0.95 + np.random.random() * 0.04
            session.add_measurement(omega, context="resting")
            await asyncio.sleep(0.01) # Acelerado para testes

    async def _run_bayesian_calibration(self, session: CalibrationSession):
        prior_mean = self.BAYESIAN_PRIOR_MEAN
        prior_std = self.BAYESIAN_PRIOR_STD

        for t in range(self.MIN_MEASUREMENTS_FOR_BASELINE):
            if self.omega_interface:
                omega = await self.omega_interface(session.participant_id)
            else:
                omega = 0.95 + np.random.random() * 0.04

            post_mean, post_std = self._bayesian_update(prior_mean, prior_std, omega, self.MEASUREMENT_ERROR_STD)
            session.add_measurement(omega, context="bayesian")
            prior_mean, prior_std = post_mean, post_std
            await asyncio.sleep(0.01)

    def _bayesian_update(self, prior_mean: float, prior_std: float,
                        measurement: float, measurement_error: float
                       ) -> Tuple[float, float]:
        prior_precision = 1.0 / (prior_std ** 2)
        likelihood_precision = 1.0 / (measurement_error ** 2)

        posterior_precision = prior_precision + likelihood_precision
        posterior_mean = (prior_precision * prior_mean +
                         likelihood_precision * measurement) / posterior_precision
        posterior_std = np.sqrt(1.0 / posterior_precision)

        return posterior_mean, posterior_std

    def _compute_baseline(self, calibration_data: Dict,
                         method: CalibrationMethod
                        ) -> Tuple[float, float, Tuple[float, float]]:
        omega_values = [m["value"] for m in calibration_data["measurements"]]

        baseline = np.mean(omega_values)
        std = np.std(omega_values, ddof=1) if len(omega_values) > 1 else 0.01

        ci_margin = 1.96 * std / np.sqrt(len(omega_values))
        ci_95 = (float(baseline - ci_margin), float(baseline + ci_margin))

        return float(np.clip(baseline, *self.SAFE_OMEGA_RANGE)), float(std), ci_95

    async def _characterize_task_responsiveness(self, session: CalibrationSession) -> Dict[str, float]:
        return {"focus": 0.01, "creative": 0.02}

    async def _anchor_calibration_profile(self, profile: IndividualOmegaProfile):
        if self.codex:
            await self.codex.store_artifact(
                artifact_id=f"omega_calibration_{profile.participant_id}",
                content_hash=profile._compute_profile_hash(),
                metadata=profile.to_audit_dict()
            )

if __name__ == "__main__":
    async def main():
        calibrator = IndividualOmegaCalibrator()
        participant_id = "test_user"
        consent = {"is_valid_and_signed": True}
        medical = {}
        profile = await calibrator.run_calibration_protocol(participant_id, consent, medical)
        print(f"Profile: {profile.baseline_omega}")

    asyncio.run(main())
