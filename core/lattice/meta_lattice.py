from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
import math
import numpy as np
import hashlib
import time
from collections import deque


@dataclass
class MultiModalPhaseAlignedStateVector:
    collaborative_phase: float
    participant_phases: Dict[str, float]

def extract_participant_phase(phase_vector: MultiModalPhaseAlignedStateVector, participant_id: str) -> float:
    return phase_vector.participant_phases.get(participant_id, 0.0)

def compute_inter_face_epsilon(pv1: MultiModalPhaseAlignedStateVector, pv2: MultiModalPhaseAlignedStateVector) -> float:
    # A mock calculation for inter-face epsilon
    diff = abs(pv1.collaborative_phase - pv2.collaborative_phase)
    return diff / 2.0 + 0.04

def phase_distance(pv1: MultiModalPhaseAlignedStateVector, pv2: MultiModalPhaseAlignedStateVector) -> float:
    diff = abs(pv1.collaborative_phase - pv2.collaborative_phase)
    return min(diff, 2*np.pi - diff)


@dataclass
class MetaLatticeStateVector:
    """Represents a triangular face in the meta-lattice."""

    # Identity
    face_id: str  # SHA-256(participant_A_DID + participant_B_DID + collaborative_space_id)
    participants: Tuple[str, str]  # Participant DIDs
    collaborative_space_id: str

    # Phase geometry (from MM-PASV of the face)
    phase_vector: MultiModalPhaseAlignedStateVector

    # Meta-connectivity
    connected_faces: List[str] = field(default_factory=list)  # IDs of adjacent faces in meta-lattice
    connection_weights: Dict[str, float] = field(default_factory=dict)  # Strength of connection (based on phase coherence)

    # Global invariants
    global_epsilon: float = 0.0472  # Inter-triad phase variance (must be in [0.04, 0.10])
    global_pdi_consensus: float = 1.0  # Weighted PDI across meta-lattice

    # Integrity
    state_hash: str = ""
    prev_state_hash: str = ""

    def is_orthogonal_compatible(self, other: 'MetaLatticeStateVector') -> bool:
        """Checks if two faces can connect in the meta-lattice."""
        # 1. Shared participant orthogonality
        shared = set(self.participants) & set(other.participants)
        if shared:
            participant = shared.pop()
            phase_self = extract_participant_phase(self.phase_vector, participant)
            phase_other = extract_participant_phase(other.phase_vector, participant)
            phase_diff = abs(phase_self - phase_other)
            phase_diff = min(phase_diff, 2*np.pi - phase_diff)
            if phase_diff < 0.03 or phase_diff > 0.15:
                return False

        # 2. Collaborative space orthogonality
        collab_diff = abs(self.phase_vector.collaborative_phase -
                         other.phase_vector.collaborative_phase)
        collab_diff = min(collab_diff, 2*np.pi - collab_diff)
        if collab_diff < 0.03 or collab_diff > 0.15:
            return False

        # 3. Global mercy gap preservation
        inter_epsilon = compute_inter_face_epsilon(self.phase_vector, other.phase_vector)
        if not (0.04 <= inter_epsilon <= 0.10):
            return False

        # 4. PDI compatibility
        if abs(self.global_pdi_consensus - other.global_pdi_consensus) > 0.2:
            return False

        return True


def compute_connection_weight(face_a: MetaLatticeStateVector, face_b: MetaLatticeStateVector) -> float:
    return 1.0 / (1.0 + phase_distance(face_a.phase_vector, face_b.phase_vector))

def mutual_agreement(proposal: dict) -> bool:
    return True

def compute_weighted_epsilon(e1: float, e2: float, weight: float) -> float:
    return e1 * 0.5 + e2 * 0.5

def compute_weighted_pdi(p1: float, p2: float, weight: float) -> float:
    return p1 * 0.5 + p2 * 0.5

def log_face_connection_vc(face_a: MetaLatticeStateVector, face_b: MetaLatticeStateVector, proposal: dict):
    pass

def send_mlsv(peer_id: str, mlsv: MetaLatticeStateVector):
    pass


class MetaLatticeGossip:
    def __init__(self, participant_id: str, local_face: MetaLatticeStateVector):
        self.participant_id = participant_id
        self.local_face = local_face
        self.peer_buffer = {}  # peer_id -> deque of MLSV

    def broadcast_state(self, peer_subset: List[str]):
        """Broadcasts local MLSV to a random subset of peers."""
        for peer in peer_subset:
            send_mlsv(peer, self.local_face)

    def receive_state(self, peer_id: str, mlsv: MetaLatticeStateVector):
        """Processes incoming MLSV from peer."""
        # Buffer state
        if peer_id not in self.peer_buffer:
            self.peer_buffer[peer_id] = deque(maxlen=10)
        self.peer_buffer[peer_id].append(mlsv)

        # Check for orthogonal connection
        latest_peer = self.peer_buffer[peer_id][-1]
        if self.local_face.is_orthogonal_compatible(latest_peer):
            # Propose connection
            connection_proposal = {
                "face_a": self.local_face.face_id,
                "face_b": latest_peer.face_id,
                "connection_weight": compute_connection_weight(self.local_face, latest_peer),
                "timestamp": time.time()
            }
            # Mutual agreement required
            if mutual_agreement(connection_proposal):
                self._establish_connection(latest_peer, connection_proposal)

    def _establish_connection(self, other_face: MetaLatticeStateVector, proposal: dict):
        """Establishes connection between two faces."""
        # Update local face's connected_faces
        if other_face.face_id not in self.local_face.connected_faces:
            self.local_face.connected_faces.append(other_face.face_id)
            self.local_face.connection_weights[other_face.face_id] = proposal["connection_weight"]

            # Recompute global invariants (weighted average preserving mercy gap)
            self.local_face.global_epsilon = compute_weighted_epsilon(
                self.local_face.global_epsilon,
                other_face.global_epsilon,
                self.local_face.connection_weights[other_face.face_id]
            )
            self.local_face.global_pdi_consensus = compute_weighted_pdi(
                self.local_face.global_pdi_consensus,
                other_face.global_pdi_consensus,
                self.local_face.connection_weights[other_face.face_id]
            )

            # Log connection to ethical ledger as VC
            log_face_connection_vc(self.local_face, other_face, proposal)


def compute_phase_centroid(faces: List[MetaLatticeStateVector]) -> MultiModalPhaseAlignedStateVector:
    avg_collab = sum(f.phase_vector.collaborative_phase for f in faces) / len(faces)
    return MultiModalPhaseAlignedStateVector(avg_collab, {})

def generate_cluster_id() -> str:
    return "cluster_" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]

def compute_cluster_epsilon(faces: List[MetaLatticeStateVector]) -> float:
    return sum(f.global_epsilon for f in faces) / len(faces)

def compute_cluster_pdi(faces: List[MetaLatticeStateVector]) -> float:
    return sum(f.global_pdi_consensus for f in faces) / len(faces)

def select_representative_face(faces: List[MetaLatticeStateVector]) -> str:
    return faces[0].face_id

@dataclass
class ClusterStateVector:
    cluster_id: str
    phase_centroid: MultiModalPhaseAlignedStateVector
    global_epsilon: float
    global_pdi: float
    face_count: int
    representative_face: str


class HierarchicalMetaLattice:
    def __init__(self, cluster_radius: float = 0.1):
        self.cluster_radius = cluster_radius  # Phase similarity threshold for clustering
        self.clusters = {}  # cluster_id -> List[MetaLatticeStateVector]

    def assign_to_cluster(self, mlsv: MetaLatticeStateVector) -> str:
        """Assigns a face to a cluster based on phase similarity."""
        # Compute phase centroid for each existing cluster
        for cluster_id, faces in self.clusters.items():
            centroid = compute_phase_centroid(faces)
            if phase_distance(mlsv.phase_vector, centroid) < self.cluster_radius:
                self.clusters[cluster_id].append(mlsv)
                return cluster_id

        # Create new cluster
        cluster_id = generate_cluster_id()
        self.clusters[cluster_id] = [mlsv]
        return cluster_id

    def aggregate_cluster_state(self, cluster_id: str) -> ClusterStateVector:
        """Aggregates cluster-level state for inter-cluster gossip."""
        faces = self.clusters[cluster_id]
        return ClusterStateVector(
            cluster_id=cluster_id,
            phase_centroid=compute_phase_centroid(faces),
            global_epsilon=compute_cluster_epsilon(faces),
            global_pdi=compute_cluster_pdi(faces),
            face_count=len(faces),
            representative_face=select_representative_face(faces)
        )
