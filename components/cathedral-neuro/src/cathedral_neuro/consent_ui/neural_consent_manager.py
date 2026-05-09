"""
neural_consent_manager.py — Gerenciador de consentimento granular
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field

@dataclass
class NeuralConsentScope:
    consent_id: str
    participant_did: str
    channels: List[str]
    intention_types: List[str]
    contexts: List[str]
    duration: Dict
    revocable: bool
    revocable_by_neural_command: bool
    granted_at: float = field(default_factory=time.time)
    revoked_at: Optional[float] = None

    def is_active(self):
        return self.revoked_at is None

    def to_dict(self):
        return {"consent_id": self.consent_id, "channels": self.channels}

class NeuralConsentManager:
    def __init__(self, codex_client, participant_did):
        self.codex = codex_client
        self.participant_did = participant_did
        self._active_consents: Dict[str, NeuralConsentScope] = {}
        self._on_revocation_callback = None

    async def grant_consent(self, channels, intention_types, contexts, duration, revocable_by_neural_command=True, neural_revocation_pattern=None):
        consent_id = f"consent_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"
        scope = NeuralConsentScope(consent_id, self.participant_did, channels, intention_types, contexts, duration, True, revocable_by_neural_command)
        self._active_consents[consent_id] = scope
        return scope

    async def check_consent(self, channel, intention_type, context):
        for c in self._active_consents.values():
            if channel in c.channels and intention_type in c.intention_types and context in c.contexts and c.is_active():
                return c
        return None

    def on_neural_revocation_detected(self, callback):
        self._on_revocation_callback = callback
