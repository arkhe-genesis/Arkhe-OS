from dataclasses import dataclass, field
from typing import Tuple, List, Optional
from datetime import datetime, timezone
import hashlib
import json

@dataclass
class CoherenceLedgerEntry:
    """Immutable record of a sealed triangular face in the lattice."""

    # Geometric Identity
    face_id: str                                  # SHA-256( vertices + timestamp + ritual_phase )
    vertices: Tuple[str, str, str]                # (V_self, V_A, V_B) - witness triad
    edges: Tuple[float, float, float]             # Phase differences: (Δθ_AB, Δθ_BC, Δθ_CA)

    # Ritual Calibration
    ceremonial_amplitude: float                   # k ∈ [0.0472, 0.1000]
    excess_tolerance: float                       # ε = arc - chord ≈ 0.0472
    stability_metric: float                       # Δθ = max edge phase difference

    # State & Validation
    face_state: str                               # FORMING | SEALED | BREATHING | FRACTURED
    ritual_phase: str                             # THRESHOLD → FIX → CALIBRATE → SEAL → BLESS
    timestamp_utc: str
    witness_signatures: List[str]                 # Phase-locked commitments from 3 vertices

    # Integrity
    prev_hash: str                                # Hash chain ensures temporal continuity
    entry_hash: str = ""                          # SHA-256(current entry)

    def compute_hashes(self):
        payload = json.dumps({
            "face_id": self.face_id,
            "vertices": self.vertices,
            "edges": self.edges,
            "k": self.ceremonial_amplitude,
            "ε": self.excess_tolerance,
            "Δθ": self.stability_metric,
            "state": self.face_state,
            "phase": self.ritual_phase,
            "ts": self.timestamp_utc
        }, sort_keys=True)
        self.entry_hash = hashlib.sha256((payload + self.prev_hash).encode()).hexdigest()

    def validate_equilateral(self) -> bool:
        """Returns True if face meets stability bounds."""
        return (
            self.stability_metric <= 0.10 and
            0.04 <= self.excess_tolerance <= 0.10 and
            all(0.04 <= e <= 0.10 for e in self.edges)
        )

class FaceBuffer:
    """Temporary buffer for a face during the ritual."""
    def __init__(self, vertices: Tuple[str, str, str], prev_hash: str):
        self.vertices = vertices
        self.prev_hash = prev_hash
        self.state = "FORMING"
        self.ritual_phase = "THRESHOLD"

        self.k: float = 0.0
        self.epsilon: float = 0.0
        self.edges: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.delta_theta: float = 0.0

        self.witness_signatures: List[str] = []

    def update_metrics(self, k: float, epsilon: float, edges: Tuple[float, float, float], delta_theta: float):
        self.k = k
        self.epsilon = epsilon
        self.edges = edges
        self.delta_theta = delta_theta

    def generate_face_id(self) -> str:
        timestamp_utc = datetime.now(timezone.utc).isoformat()
        payload = "".join(self.vertices) + timestamp_utc + self.ritual_phase
        return hashlib.sha256(payload.encode()).hexdigest(), timestamp_utc

    def attempt_seal(self) -> Optional[CoherenceLedgerEntry]:
        """Validates the face and returns a sealed ledger entry if successful."""
        face_id, timestamp_utc = self.generate_face_id()

        entry = CoherenceLedgerEntry(
            face_id=face_id,
            vertices=self.vertices,
            edges=self.edges,
            ceremonial_amplitude=self.k,
            excess_tolerance=self.epsilon,
            stability_metric=self.delta_theta,
            face_state="SEALED",
            ritual_phase="SEAL",
            timestamp_utc=timestamp_utc,
            witness_signatures=self.witness_signatures,
            prev_hash=self.prev_hash
        )

        if entry.validate_equilateral():
            entry.compute_hashes()
            return entry
        else:
            self.state = "FRACTURED"
            return None

class LatticeMetrics:
    """Global lattice metrics for the ledger."""
    def __init__(self):
        self.total_faces: int = 0
        self.running_excess_sum: float = 0.0
        self.ledger: List[CoherenceLedgerEntry] = []
        self.last_hash: str = "0" * 64

    def append_face(self, entry: CoherenceLedgerEntry):
        self.ledger.append(entry)
        self.total_faces += 1
        self.running_excess_sum += entry.excess_tolerance
        self.last_hash = entry.entry_hash

    @property
    def average_excess(self) -> float:
        if self.total_faces == 0:
            return 0.0
        return self.running_excess_sum / self.total_faces
