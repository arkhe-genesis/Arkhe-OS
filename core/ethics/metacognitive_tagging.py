import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class MetacognitiveTag:
    """Cryptographically binds qualitative insight and consent to a ledger entry."""
    subject_id: str
    ledger_entry_hash: str     # The exact face/hash this tag binds to
    qualitative_insight: str   # E.g., "Deep REM recall", "Mild rigidity in pre-frontal"
    consent_state: bool        # True if subject consents to ongoing mapping
    timestamp_utc: float

    # Signatures
    subject_signature: str = "" # In production: ECDSA sig from subject's key
    tag_hash: str = ""

    def compute_hash(self):
        payload = json.dumps({
            "subject": self.subject_id,
            "entry_hash": self.ledger_entry_hash,
            "insight": self.qualitative_insight,
            "consent": self.consent_state,
            "ts": self.timestamp_utc
        }, sort_keys=True)
        self.tag_hash = hashlib.sha256(payload.encode()).hexdigest()

class LongitudinalEthicsTracker:
    """Tracks the continuous ethical validity across the ledger hash chain."""

    def __init__(self):
        # map ledger_entry_hash -> List of MetacognitiveTags
        self.tags_by_entry: Dict[str, List[MetacognitiveTag]] = {}

        # map subject_id -> List of MetacognitiveTags (chronological)
        self.tags_by_subject: Dict[str, List[MetacognitiveTag]] = {}

    def append_tag(self, tag: MetacognitiveTag):
        if not tag.tag_hash:
            tag.compute_hash()

        if tag.ledger_entry_hash not in self.tags_by_entry:
            self.tags_by_entry[tag.ledger_entry_hash] = []
        self.tags_by_entry[tag.ledger_entry_hash].append(tag)

        if tag.subject_id not in self.tags_by_subject:
            self.tags_by_subject[tag.subject_id] = []
        self.tags_by_subject[tag.subject_id].append(tag)

    def verify_longitudinal_continuity(self, subject_id: str) -> bool:
        """
        Validates that the subject maintains active consent across the chain.
        Returns False if the chain of consent is broken or revoked.
        """
        if subject_id not in self.tags_by_subject:
            return False # No history = no consent continuity

        tags = self.tags_by_subject[subject_id]

        # Chronological verification
        # Assuming they are appended chronologically.
        for tag in tags:
            # Re-verify the hash to ensure the tag wasn't altered
            recomputed = hashlib.sha256(json.dumps({
                "subject": tag.subject_id,
                "entry_hash": tag.ledger_entry_hash,
                "insight": tag.qualitative_insight,
                "consent": tag.consent_state,
                "ts": tag.timestamp_utc
            }, sort_keys=True).encode()).hexdigest()

            if recomputed != tag.tag_hash:
                return False # Tampered!

            if not tag.consent_state:
                return False # Consent revoked at this point in the longitudinal arc

        return True
