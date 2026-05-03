from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime
import hashlib
import json
import time

def participant_sign(hash_str: str) -> str:
    # A mock function to simulate ECDSA signature by a participant
    return f"sig_{hash_str}"

def verify_participant_signature(hash_str: str, signature: str) -> bool:
    # A mock verification of the simulated signature
    return signature == f"sig_{hash_str}"

@dataclass
class MetacognitiveTag:
    session_hash: str
    tag_type: str
    tag_value: float
    narrative_note: Optional[str]
    timestamp: float
    participant_signature: str

    def compute_tag_hash(self) -> str:
        """Creates Merkle-proof-compatible hash for tag verification."""
        payload = json.dumps({
            "session_hash": self.session_hash,
            "tag_type": self.tag_type,
            "tag_value": self.tag_value,
            "narrative_note": self.narrative_note,
            "timestamp": self.timestamp
        }, sort_keys=True)
        return hashlib.sha256((payload + self.participant_signature).encode()).hexdigest()

@dataclass
class RevocationProof:
    token_hash: str
    revocation_hash: str
    timestamp: float
    participant_signature: str

class ConsentToken:
    def __init__(self, participant_id: str, researcher_id: str, scope: Dict[str, bool], expiry: datetime):
        self.participant_id = participant_id
        self.researcher_id = researcher_id
        self.scope = scope
        self.expiry = expiry

        self.token_hash = hashlib.sha256(f"{participant_id}:{researcher_id}:{json.dumps(scope, sort_keys=True)}:{expiry.isoformat()}".encode()).hexdigest()
        self.signature = participant_sign(self.token_hash)
        self.revoked = False

    def is_valid(self, request_timestamp: datetime, requested_data_type: str) -> bool:
        """Validates token for specific data request."""
        if self.revoked:
            return False

        if request_timestamp > self.expiry:
            return False

        if requested_data_type not in self.scope or not self.scope[requested_data_type]:
            return False

        return verify_participant_signature(self.token_hash, self.signature)

    def revoke(self) -> RevocationProof:
        """Creates cryptographic proof of revocation for audit trail."""
        self.revoked = True
        revocation_hash = hashlib.sha256(f"REVOKED:{self.token_hash}:{time.time()}".encode()).hexdigest()
        return RevocationProof(
            token_hash=self.token_hash,
            revocation_hash=revocation_hash,
            timestamp=time.time(),
            participant_signature=participant_sign(revocation_hash)
        )
