"""
committee_onboarding.py — Onboarding de membros do comitê de ética
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

class CommitteeRole(Enum):
    CHAIR = "chair"
    MEMBER = "member"
    TECHNICAL_EXPERT = "technical_expert"
    PATIENT_ADVOCATE = "patient_advocate"

@dataclass
class CommitteeMemberCredential:
    credential_id: str
    member_did: str
    role: CommitteeRole
    institution: str
    credentials: List[str]
    issued_at: float

class EthicsCommitteeRegistry:
    def __init__(self, committee_id, name, institution, charter_hash, members, quorum_size, created_at):
        self.committee_id = committee_id
        self.name = name
        self.institution = institution
        self.charter_hash = charter_hash
        self.members = members
        self.quorum_size = quorum_size
        self.created_at = created_at
        self.registry_hash = "hash"

    def add_member(self, credential):
        self.members[credential.member_did] = credential
        return True

    def get_active_members(self):
        return list(self.members.values())

    def has_quorum(self):
        return len(self.members) >= self.quorum_size

class EthicsCommitteeOnboarding:
    def __init__(self, codex_client, did_manager, committee_registry):
        self.codex = codex_client
        self.did_manager = did_manager
        self.registry = committee_registry

    async def onboard_member(self, candidate_did, role, institution, credentials, issuer_did, issuer_signature, charter_acceptance):
        credential = CommitteeMemberCredential(f"cred_{candidate_did[:8]}", candidate_did, role, institution, credentials, time.time())
        self.registry.add_member(credential)
        return credential

    def get_committee_composition(self, include_sensitive=False):
        active = self.registry.get_active_members()
        return {
            "name": self.registry.name,
            "institution": self.registry.institution,
            "n_active_members": len(active),
            "quorum_size": self.registry.quorum_size,
            "has_quorum": self.registry.has_quorum(),
            "roles_distribution": {}
        }
