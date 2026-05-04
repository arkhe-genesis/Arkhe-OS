import pytest
import math
from core.protocol.multi_subject_lattice_protocol import MultiSubjectLatticeProtocol, MultiSubjectNode

def test_multi_subject_registration():
    protocol = MultiSubjectLatticeProtocol()
    protocol.register_subject("subj1", 0.5)
    protocol.register_subject("subj2", 1.5)

    assert len(protocol.nodes) == 2
    assert "subj1" in protocol.nodes
    assert protocol.nodes["subj1"].theta == 0.5

def test_collision_detection():
    protocol = MultiSubjectLatticeProtocol(collision_threshold=0.2)
    # These two are too close (0.1 difference)
    protocol.register_subject("subj1", 0.5)
    protocol.register_subject("subj2", 0.6)

    # This one is far away
    protocol.register_subject("subj3", 1.5)

    collisions = protocol.detect_collisions()

    assert len(collisions) == 1
    # Check if the colliding pair is subj1 and subj2
    pair = collisions[0]
    assert set(pair) == {"subj1", "subj2"}

def test_collision_resolution():
    protocol = MultiSubjectLatticeProtocol(collision_threshold=0.2)
    protocol.register_subject("subj1", 0.5)
    protocol.register_subject("subj2", 0.6) # distance is 0.1

    # Initial states
    node1 = protocol.nodes["subj1"]
    node2 = protocol.nodes["subj2"]

    assert node1.k == 0.0750
    assert node2.k == 0.0750

    # Resolve
    protocol.step()

    # They should be pushed apart.
    # The shift is 0.2 / 2.0 = 0.1
    # subj2 is > subj1, so subj2 shifts +0.1, subj1 shifts -0.1
    assert round(node1.theta, 2) == 0.40
    assert round(node2.theta, 2) == 0.70

    # Amplitude dampened (0.075 * 0.9 = 0.0675)
    assert round(node1.k, 4) == 0.0675
    assert round(node2.k, 4) == 0.0675

    # Ensure they no longer collide
    assert len(protocol.detect_collisions()) == 0

def test_collision_resolution_cyclic_boundary():
    protocol = MultiSubjectLatticeProtocol(collision_threshold=0.2)
    # 0.05 and 6.20 are close in cyclic space (difference is ~0.13 < 0.20)
    protocol.register_subject("subj1", 0.05)
    protocol.register_subject("subj2", 6.20)

    assert len(protocol.detect_collisions()) == 1

    # Resolve
    protocol.step()

    # They should be pushed apart.
    # cyclic_diff(0.05, 6.20) is positive (0.13), so subj1 is ahead and gets +0.1, subj2 gets -0.1
    # 0.05 + 0.1 = 0.15
    # 6.20 - 0.1 = 6.10
    node1 = protocol.nodes["subj1"]
    node2 = protocol.nodes["subj2"]

    assert round(node1.theta, 2) == 0.15
    assert round(node2.theta, 2) == 6.10

    # Ensure they no longer collide
    assert len(protocol.detect_collisions()) == 0
