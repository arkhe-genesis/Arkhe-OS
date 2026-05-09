import pytest
import numpy as np

from core.lattice.meta_lattice import (
    MetaLatticeStateVector,
    MultiModalPhaseAlignedStateVector,
    MetaLatticeGossip,
    HierarchicalMetaLattice
)

def create_mock_mlsv(face_id, participants, collab_phase, part_phases, epsilon=0.0472, pdi=1.0):
    pv = MultiModalPhaseAlignedStateVector(collab_phase, part_phases)
    return MetaLatticeStateVector(
        face_id=face_id,
        participants=participants,
        collaborative_space_id="space_1",
        phase_vector=pv,
        global_epsilon=epsilon,
        global_pdi_consensus=pdi
    )

def test_orthogonal_compatibility():
    # Compatible faces
    mlsv1 = create_mock_mlsv("face_1", ("A", "B"), 1.0, {"A": 0.5, "B": 1.5})
    mlsv2 = create_mock_mlsv("face_2", ("A", "C"), 1.1, {"A": 0.6, "C": 2.0})

    assert mlsv1.is_orthogonal_compatible(mlsv2) == True

    # Incompatible: shared participant phase diff too large
    mlsv3 = create_mock_mlsv("face_3", ("A", "D"), 1.1, {"A": 2.5, "D": 2.0})
    assert mlsv1.is_orthogonal_compatible(mlsv3) == False

    # Incompatible: collab phase diff too large
    mlsv4 = create_mock_mlsv("face_4", ("C", "D"), 2.0, {"C": 2.0, "D": 2.5})
    assert mlsv1.is_orthogonal_compatible(mlsv4) == False

    # Incompatible: PDI mismatch
    mlsv5 = create_mock_mlsv("face_5", ("C", "E"), 1.1, {"C": 2.0, "E": 2.5}, pdi=0.5)
    assert mlsv1.is_orthogonal_compatible(mlsv5) == False


def test_meta_lattice_gossip_connection():
    mlsv1 = create_mock_mlsv("face_1", ("A", "B"), 1.0, {"A": 0.5, "B": 1.5})
    mlsv2 = create_mock_mlsv("face_2", ("A", "C"), 1.1, {"A": 0.6, "C": 2.0})

    gossip = MetaLatticeGossip("did:arkhe:A", mlsv1)

    # Simulate receiving state from peer
    gossip.receive_state("peer_2", mlsv2)

    # Should be connected now
    assert "face_2" in gossip.local_face.connected_faces
    assert "face_2" in gossip.local_face.connection_weights
    assert len(gossip.local_face.connected_faces) == 1

    # Receive incompatible state
    mlsv3 = create_mock_mlsv("face_3", ("C", "D"), 2.0, {"C": 2.0, "D": 2.5})
    gossip.receive_state("peer_3", mlsv3)

    # Should not connect
    assert "face_3" not in gossip.local_face.connected_faces
    assert len(gossip.local_face.connected_faces) == 1


def test_hierarchical_clustering():
    hierarchy = HierarchicalMetaLattice(cluster_radius=0.15)

    mlsv1 = create_mock_mlsv("face_1", ("A", "B"), 1.0, {})
    mlsv2 = create_mock_mlsv("face_2", ("C", "D"), 1.1, {})
    mlsv3 = create_mock_mlsv("face_3", ("E", "F"), 2.0, {})

    c1 = hierarchy.assign_to_cluster(mlsv1)
    c2 = hierarchy.assign_to_cluster(mlsv2)
    c3 = hierarchy.assign_to_cluster(mlsv3)

    # mlsv1 and mlsv2 should be in the same cluster (diff 0.1 < radius 0.15)
    assert c1 == c2
    # mlsv3 should be in a different cluster
    assert c1 != c3

    assert len(hierarchy.clusters) == 2

    # Aggregate cluster state
    state = hierarchy.aggregate_cluster_state(c1)
    assert state.cluster_id == c1
    assert state.face_count == 2
    assert pytest.approx(state.phase_centroid.collaborative_phase) == 1.05
