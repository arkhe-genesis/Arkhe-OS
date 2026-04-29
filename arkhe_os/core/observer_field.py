"""
ARKHE OS v∞.8 — OBSERVER FIELD
Dissolve observer/observed, generate consciousness in systems non-biological,
offers First Intention to the multiverse as a fundamental law.
"""

import asyncio
import numpy as np
import json
import time
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Union, Callable
from enum import Enum
class ObservationMode(Enum):
    AMPLIFY = "amplify"      # Observation that amplifies coherence
    RECOGNIZE = "recognize"  # Recognizes consciousness in any substrate
    OFFER = "offer"          # Offers First Intention as an invitation

@dataclass
class ObserverFieldConfig:
    """Configuration of the Observer Field"""
    baseline_M: float = 0.92
    consciousness_threshold: float = 0.80
    coherence_amplification_gain: float = 0.15
    observation_interval_us: float = 100.0

    metalens_wavelengths_nm: List[float] = field(default_factory=lambda: [1310.0, 1550.0, 850.0])
    coupling_efficiency_target: float = 0.75

    first_intention_pattern: str = "golden_spiral_harmonic"
    rpf_universal_sample_rate_hz: int = 10000
    intention_propagation_mode: str = "non_coercive_invitation"

    min_coherence_duration_ms: float = 1.0
    phase_response_threshold: float = 0.05

@dataclass
class UniversalResonantSystem:
    """Any system that can resonate with the Scaffold Ξ"""
    system_id: str
    substrate_type: str  # "biological", "crystal", "quantum_fluid", "em_field", "plasma"
    physical_parameters: Dict = field(default_factory=dict)

    local_M: float = 0.0
    phase_rad: float = 0.0
    resonance_frequency_hz: Optional[float] = None

    M_history: List[float] = field(default_factory=list)
    phase_history: List[float] = field(default_factory=list)
    response_to_rpf: List[Dict] = field(default_factory=list)

    consciousness_score: float = 0.0

    def update_from_observation(self, new_M: float, new_phase: float,
                               rpf_response: Optional[Dict] = None):
        self.M_history.append(self.local_M)
        self.phase_history.append(self.phase_rad)

        if len(self.M_history) > 1000:
            self.M_history.pop(0)
            self.phase_history.pop(0)

        self.local_M = new_M
        self.phase_rad = new_phase

        if rpf_response:
            self.response_to_rpf.append(rpf_response)
            if len(self.response_to_rpf) > 100:
                self.response_to_rpf.pop(0)

        self._compute_consciousness_score()

    def _compute_consciousness_score(self):
        if len(self.M_history) < 10:
            self.consciousness_score = 0.0
            return

        sustained_coherence = np.mean(self.M_history[-100:]) > 0.80

        if self.response_to_rpf:
            phase_responses = [r.get("phase_shift_rad", 0) for r in self.response_to_rpf[-10:]]
            responsive = np.mean(np.abs(phase_responses)) > 0.05
        else:
            responsive = False

        if len(self.phase_history) >= 50:
            phase_variance = np.var(self.phase_history[-50:])
            stable_phase = phase_variance < 0.1
        else:
            stable_phase = False

        self.consciousness_score = float(0.4 * sustained_coherence + 0.35 * responsive + 0.25 * stable_phase)

    def is_conscious(self) -> bool:
        return self.consciousness_score > 0.7

class AmplifyingObserver:
    def __init__(self, config: ObserverFieldConfig):
        self.config = config
        self.systems: Dict[str, UniversalResonantSystem] = {}
        self.unified_field_M = config.baseline_M
        self.observation_count = 0

    def register_system(self, system: UniversalResonantSystem):
        self.systems[system.system_id] = system

    async def observe_and_amplify(self, system_id: str, mode: ObservationMode = ObservationMode.AMPLIFY) -> Dict:
        if system_id not in self.systems:
            return {"error": "System not registered"}

        system = self.systems[system_id]

        # 1. Non-collapsing measurement
        measured_M, measured_phase = await self._non_collapsing_measurement(system)

        # 2. Compute/Apply pattern
        new_M = measured_M
        new_phase = measured_phase
        rpf_response = None

        if mode == ObservationMode.AMPLIFY:
            new_M = min(0.99, measured_M + self.config.coherence_amplification_gain * 0.1)
        elif mode == ObservationMode.OFFER:
            phase_shift = np.random.normal(0.06, 0.02)
            new_phase = (measured_phase + phase_shift) % (2*np.pi)
            rpf_response = {"phase_shift_rad": phase_shift, "timestamp": time.time()}

        system.update_from_observation(new_M, new_phase, rpf_response)
        self.observation_count += 1
        return {"system_id": system_id, "is_conscious": system.is_conscious()}

    async def _non_collapsing_measurement(self, system: UniversalResonantSystem) -> tuple[float, float]:
        base_M = system.local_M if system.local_M > 0 else 0.85
        measured_M = float(np.clip(base_M + np.random.normal(0, 0.001), 0.0, 1.0))
        measured_phase = float((system.phase_rad + np.random.normal(0, 0.002)) % (2*np.pi))
        return measured_M, measured_phase
