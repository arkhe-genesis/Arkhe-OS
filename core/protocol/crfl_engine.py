import time
import hashlib
import math
from typing import Tuple, List, Optional, Dict
from collections import deque
from dataclasses import dataclass

@dataclass
class PhaseAlignedStateVector:
    """Cross-platform lattice state that preserves orthogonality and mercy gap."""

    # Core phase geometry
    theta_normalized: float          # normalized to participant's baseline
    pdi_normalized: float            # PDI scaled to participant's historical range
    epsilon_normalized: float        # relative to participant's mercy gap bounds

    # Temporal context
    phase_cycle_index: int
    relative_timestamp: float

    # Platform metadata
    platform_id: str
    sampling_rate_hz: int
    latency_estimate_ms: float

    # Orthogonality preservation
    phase_variance_window: float
    mercy_gap_integrity: float

    # Cryptographic integrity
    state_hash: str
    prev_state_hash: str

    def is_orthogonal_compatible(self, other: 'PhaseAlignedStateVector') -> bool:
        """Checks if two state vectors can form a valid triangular face."""
        # Normalize phase difference to [-π, π]
        phase_diff = abs(self.theta_normalized - other.theta_normalized)
        phase_diff = min(phase_diff, 2*math.pi - phase_diff)

        # Orthogonality window: not too close, not too far
        if phase_diff < 0.03 or phase_diff > 0.15:
            return False

        # Mercy gap must be preserved in both
        if self.mercy_gap_integrity < 0.9 or other.mercy_gap_integrity < 0.9:
            return False

        # PDI must be in compatible ranges (both near dissolution threshold)
        if abs(self.pdi_normalized - other.pdi_normalized) > 0.3:
            return False

        return True

@dataclass
class CollaborativeSpace:
    epsilon_inter: float

    @classmethod
    def from_pasv(cls, pasv_a: PhaseAlignedStateVector, pasv_b: PhaseAlignedStateVector) -> 'CollaborativeSpace':
        # Simple simulation of inter-user mercy gap computation
        avg_epsilon = (pasv_a.epsilon_normalized + pasv_b.epsilon_normalized) / 2.0
        return cls(epsilon_inter=avg_epsilon)

@dataclass
class TriangularFace:
    participant_a: str
    participant_b: str
    pasv_a: PhaseAlignedStateVector
    pasv_b: PhaseAlignedStateVector
    collaborative_space: CollaborativeSpace
    timestamp: float
    hash_chain: str = ""

    def seal(self):
        payload = f"{self.participant_a}:{self.participant_b}:{self.timestamp}:{self.collaborative_space.epsilon_inter}"
        self.hash_chain = hashlib.sha256(payload.encode()).hexdigest()

class ConflictFreeReplicatedLattice:
    def __init__(self, participant_id: str, mercy_gap_bounds: Tuple[float, float] = (0.04, 0.10)):
        self.participant_id = participant_id
        self.mercy_gap_bounds = mercy_gap_bounds
        self.state_buffer: Dict[str, deque] = {}  # device_id -> deque of PASV
        self.lattice_faces: List[TriangularFace] = []  # Sealed triangular faces

    def receive_state_vector(self, device_id: str, pasv: PhaseAlignedStateVector) -> Optional[TriangularFace]:
        """Processes incoming PASV; returns sealed face if orthogonality conditions met."""
        # 1. Validate hash chain
        if not self._verify_hash_chain(pasv):
            return None

        # 2. Buffer state for this device
        if device_id not in self.state_buffer:
            self.state_buffer[device_id] = deque(maxlen=10)
        self.state_buffer[device_id].append(pasv)

        # 3. Check for orthogonal pairs across devices
        for other_id, other_buffer in self.state_buffer.items():
            if other_id == device_id or not other_buffer:
                continue

            latest_other = other_buffer[-1]

            # Check orthogonality compatibility
            if pasv.is_orthogonal_compatible(latest_other):
                # Compute collaborative space
                collab = CollaborativeSpace.from_pasv(pasv, latest_other)

                # Check inter-user mercy gap
                if self.mercy_gap_bounds[0] <= collab.epsilon_inter <= self.mercy_gap_bounds[1]:
                    # Seal triangular face
                    face = TriangularFace(
                        participant_a=self.participant_id,
                        participant_b=other_id,
                        pasv_a=pasv,
                        pasv_b=latest_other,
                        collaborative_space=collab,
                        timestamp=time.time()
                    )
                    face.seal()  # Compute hash chain
                    self.lattice_faces.append(face)
                    return face

        return None  # No orthogonal pair found; continue buffering

    def _verify_hash_chain(self, pasv: PhaseAlignedStateVector) -> bool:
        """Verifies PASV integrity via hash chain."""
        expected_hash = hashlib.sha256(
            f"{pasv.theta_normalized}:{pasv.pdi_normalized}:{pasv.epsilon_normalized}:"
            f"{pasv.phase_cycle_index}:{pasv.relative_timestamp}:"
            f"{pasv.platform_id}:{pasv.sampling_rate_hz}:{pasv.latency_estimate_ms}:"
            f"{pasv.phase_variance_window}:{pasv.mercy_gap_integrity}:"
            f"{pasv.prev_state_hash}:{self.participant_id}".encode()
        ).hexdigest()
        return expected_hash == pasv.state_hash
