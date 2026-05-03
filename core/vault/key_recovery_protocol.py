import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class RecoveryShare:
    """Represents a fragmented piece of the master secret for social recovery."""
    share_id: str
    guardian_id: str
    encrypted_payload: bytes  # The share itself, encrypted for the guardian's public key
    issued_timestamp: float

@dataclass
class RecoveryRequest:
    """Represents an active attempt to recover keys."""
    request_id: str
    target_participant_id: str
    requesting_device_id: str
    collected_shares: List['RecoveryShare'] = field(default_factory=list)
    initiated_timestamp: float = field(default_factory=time.time)
    status: str = "PENDING"  # PENDING, VETOED, COMPLETED

class ParticipantKeyRecovery:
    """
    Coordinates participant-controlled social recovery.
    Ensures that social recovery happens without sovereignty loss by enforcing
    a grace period during which the original participant can veto the process.
    """

    def __init__(self, participant_id: str):
        self.participant_id = participant_id
        self.guardians: List[str] = []
        self.active_requests: Dict[str, RecoveryRequest] = {}
        self.grace_period_seconds = 86400  # 24 hours default
        self.required_shares = 3  # e.g., 3-of-5

    def setup_guardians(self, guardian_ids: List[str], required_shares: int):
        """Configure who can participate in social recovery."""
        if required_shares > len(guardian_ids):
            raise ValueError("Required shares cannot exceed number of guardians.")
        self.guardians = guardian_ids
        self.required_shares = required_shares

    def generate_shares(self, master_secret: bytes) -> List[RecoveryShare]:
        """
        Splits the master secret into shares for guardians.
        (Mock implementation of Shamir's Secret Sharing integration)
        """
        shares = []
        for i, guardian_id in enumerate(self.guardians):
            # In reality, this would use SSS to split `master_secret`
            # and encrypt the resulting share for the `guardian_id`'s public key
            mock_share_payload = hashlib.sha256(master_secret + str(i).encode()).digest()
            shares.append(RecoveryShare(
                share_id=f"share_{self.participant_id}_{i}",
                guardian_id=guardian_id,
                encrypted_payload=mock_share_payload,
                issued_timestamp=time.time()
            ))
        return shares

    def initiate_recovery(self, requesting_device_id: str) -> RecoveryRequest:
        """
        Begins the recovery process. Notifies the original device (if online)
        and starts the grace period countdown.
        """
        req_id = hashlib.sha256(f"req_{self.participant_id}_{time.time()}".encode()).hexdigest()
        req = RecoveryRequest(
            request_id=req_id,
            target_participant_id=self.participant_id,
            requesting_device_id=requesting_device_id
        )
        self.active_requests[req_id] = req
        return req

    def submit_share(self, request_id: str, share: RecoveryShare) -> bool:
        """A guardian submits their share for an active recovery request."""
        if request_id not in self.active_requests:
            return False

        req = self.active_requests[request_id]
        if req.status != "PENDING":
            return False

        # Verify share belongs to a registered guardian
        if share.guardian_id not in self.guardians:
            return False

        req.collected_shares.append(share)
        return True

    def veto_recovery(self, request_id: str) -> bool:
        """
        Original user cancels the recovery request.
        This is the core mechanic preserving sovereignty: social consensus
        cannot override the explicit refusal of the original keyholder.
        """
        if request_id in self.active_requests:
            req = self.active_requests[request_id]
            if req.status == "PENDING":
                req.status = "VETOED"
                return True
        return False

    def finalize_recovery(self, request_id: str) -> Optional[bytes]:
        """
        Attempts to combine shares to recover the master secret.
        Only succeeds if enough shares are collected AND grace period has elapsed
        WITHOUT a veto.
        """
        if request_id not in self.active_requests:
            return None

        req = self.active_requests[request_id]

        if req.status == "VETOED":
            return None

        if len(req.collected_shares) < self.required_shares:
            return None

        elapsed = time.time() - req.initiated_timestamp
        if elapsed < self.grace_period_seconds:
            # Grace period not yet over, recovery cannot be finalized to ensure veto opportunity
            return None

        req.status = "COMPLETED"
        # Mock reconstruction of master secret from shares
        reconstructed_secret = b"reconstructed_master_secret_mock"
        return reconstructed_secret
