"""
quantum_bus_publisher.py — Publicação de eventos neurais no Quantum Bus
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

class NeuralEventType(Enum):
    DECODING_RESULT = "decoding_result"
    EMERGENCY_STOP = "emergency_stop"
    NEURO_RECEIPT = "neuro_receipt"
    CONSENT_GRANT = "consent_grant"

@dataclass
class NeuralEvent:
    event_id: str
    event_type: NeuralEventType
    priority: int
    participant_did: str
    timestamp: float
    payload: Dict

    def to_grpc_message(self):
        return asdict(self)

def asdict(obj):
    from dataclasses import asdict
    return asdict(obj)

class QuantumBusNeuralPublisher:
    def __init__(self, participant_did, private_key, config=None):
        self.participant_did = participant_did
        self.private_key = private_key
        self._connected = True

    async def publish_event(self, event_type, payload, target_services, priority=None):
        print(f"📤 Published {event_type} to {target_services}")
        return f"evt_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"

    async def publish_neuro_receipt(self, receipt_data):
        return await self.publish_event(NeuralEventType.NEURO_RECEIPT, receipt_data, ["audit"])
