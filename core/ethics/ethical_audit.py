from dataclasses import dataclass
from typing import List
import hashlib
import json

@dataclass
class EthicalAuditEntry:
    researcher_id: str
    participant_root_hash: str  # Not raw data
    requested_data_types: List[str]
    consent_token_hash: str
    query_timestamp: float
    oversight_signature: str  # Signed by IRB/ethics board
    entry_hash: str = ""

    def compute_hash(self, prev_hash: str) -> str:
        payload = json.dumps({
            "researcher_id": self.researcher_id,
            "participant_root_hash": self.participant_root_hash,
            "requested_data_types": self.requested_data_types,
            "consent_token_hash": self.consent_token_hash,
            "query_timestamp": self.query_timestamp,
            "oversight_signature": self.oversight_signature,
            "prev_hash": prev_hash
        }, sort_keys=True)
        self.entry_hash = hashlib.sha256(payload.encode()).hexdigest()
        return self.entry_hash
