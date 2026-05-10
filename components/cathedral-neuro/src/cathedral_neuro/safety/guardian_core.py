"""
guardian_core.py — Safety Guardian com reflexos <50ms
"""

import asyncio
import time
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto

class SafetyTrigger(Enum):
    NEURAL_REVOCATION_COMMAND = auto()
    MOVEMENT_OUTSIDE_WORKSPACE = auto()
    CONSENT_LOST = auto()
    SIGNAL_QUALITY_DEGRADED = auto()
    DECODER_CONFIDENCE_LOW = auto()
    BIOMECHANICAL_IMPOSSIBILITY = auto()

@dataclass
class SafetyEvent:
    event_id: str
    timestamp: float
    trigger: SafetyTrigger
    severity: str
    movement_vector: Optional[List[float]]
    intervention_applied: str
    participant_did: str
    consent_id_at_time: Optional[str]
    resolution_time_ms: float

    def to_dict(self):
        return {"event_id": self.event_id, "trigger": self.trigger.name}

class SafetyGuardian:
    def __init__(self, hardware_interface, consent_manager, config=None):
        self.hardware = hardware_interface
        self.consent_manager = consent_manager
        self.config = config or {"min_signal_quality": 0.7, "min_decoder_confidence": 0.8}
        self._monitoring_active = False

    async def start_monitoring(self):
        self._monitoring_active = True

    async def validate_movement_command(self, movement_vector, participant_did, consent_id, decoder_confidence, signal_quality):
        if decoder_confidence < self.config["min_decoder_confidence"]:
            return False, None
        return True, None
