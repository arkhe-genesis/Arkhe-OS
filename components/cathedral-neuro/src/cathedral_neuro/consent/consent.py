"""
consent.py — Consentimento Neural Granular
Gestão de permissões canal-a-canal e intenção-a-intenção
"""

from typing import Dict, List, Optional, Set
import hashlib

class NeuralConsentManager:
    """Gerenciador de consentimento para BCIs soberanos."""

    def __init__(self):
        # did -> {channel: {purpose: granted}}
        self._consent_store: Dict[str, Dict[str, Dict[str, bool]]] = {}

    async def update_consent(
        self,
        participant_did: str,
        channel: str,
        purpose: str,
        granted: bool
    ):
        if participant_did not in self._consent_store:
            self._consent_store[participant_did] = {}
        if channel not in self._consent_store[participant_did]:
            self._consent_store[participant_did][channel] = {}

        self._consent_store[participant_did][channel][purpose] = granted

    async def check(
        self,
        participant_did: str,
        channel: str,
        purpose: str
    ) -> bool:
        """Verifica se há consentimento ativo para o par canal/propósito."""
        participant_data = self._consent_store.get(participant_did, {})
        channel_data = participant_data.get(channel, {})
        return channel_data.get(purpose, False)

    async def revoke_all(self, participant_did: str):
        """Revoga todos os consentimentos (Kill Switch)."""
        if participant_did in self._consent_store:
            for channel in self._consent_store[participant_did]:
                for purpose in self._consent_store[participant_did][channel]:
                    self._consent_store[participant_did][channel][purpose] = False
