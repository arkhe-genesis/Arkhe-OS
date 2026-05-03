import hashlib
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ConsentRetirementTombstone:
    """
    A cryptographic tombstone representing a retired Consent VC.
    Preserves hash chain continuity for longitudinal research,
    but explicitly revokes future raw data access.
    """
    original_vc_id: str
    revocation_hash: str
    retirement_timestamp: float
    participant_signature: str
    derivatives_hash_preservation: str  # Hash of derived insights (e.g. orthogonal witness summaries)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ConsentRetirementTombstone",
            "original_vc_id": self.original_vc_id,
            "revocation_hash": self.revocation_hash,
            "retirement_timestamp": self.retirement_timestamp,
            "participant_signature": self.participant_signature,
            "derivatives_hash_preservation": self.derivatives_hash_preservation
        }

class RevocationCascadeManager:
    """Manages the graceful retirement of VCs across the data ecosystem."""

    def __init__(self, participant_did: str):
        self.participant_did = participant_did
        self.active_vcs: Dict[str, Dict[str, Any]] = {}
        self.retired_tombstones: Dict[str, ConsentRetirementTombstone] = {}

    def register_vc(self, vc_id: str, vc_data: Dict[str, Any]):
        self.active_vcs[vc_id] = vc_data

    def retire_vc_gracefully(self, vc_id: str, derivatives_hash: str, signature: str) -> Optional[ConsentRetirementTombstone]:
        """
        Retires a VC, revoking raw data access but preserving derived research hashes.
        """
        if vc_id not in self.active_vcs:
            return None

        # Generate revocation hash
        revocation_input = f"{vc_id}:{time.time()}:{derivatives_hash}"
        revocation_hash = hashlib.sha256(revocation_input.encode()).hexdigest()

        # Create tombstone
        tombstone = ConsentRetirementTombstone(
            original_vc_id=vc_id,
            revocation_hash=revocation_hash,
            retirement_timestamp=time.time(),
            participant_signature=signature,
            derivatives_hash_preservation=derivatives_hash
        )

        # Move from active to retired
        del self.active_vcs[vc_id]
        self.retired_tombstones[vc_id] = tombstone

        return tombstone

    def verify_longitudinal_continuity(self, vc_id: str, derivatives_hash: str) -> bool:
        """
        Verifies that a derived research insight is backed by a valid (though possibly retired) VC.
        """
        if vc_id in self.active_vcs:
            return True # Still active

        if vc_id in self.retired_tombstones:
            tombstone = self.retired_tombstones[vc_id]
            # Check if the preserved derivatives hash matches the one we are verifying
            return tombstone.derivatives_hash_preservation == derivatives_hash

        return False # VC not found (neither active nor gracefully retired)
