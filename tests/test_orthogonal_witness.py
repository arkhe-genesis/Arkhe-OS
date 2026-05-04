import pytest
from core.protocol.triangular_lattice_protocol import TriangularLatticeProtocol
from core.ledger.coherence_ledger import LatticeMetrics
from core.lattice.orthogonal_witness import UserState, CollaborativeSpace

def test_lattice_protocol_single_user():
    metrics = LatticeMetrics()
    protocol = TriangularLatticeProtocol(metrics)
    protocol.initialize_ledger_buffer(("A", "B", "C"))

    # Mock states
    user_self = UserState("A", 0.9, 0.05, 0.1, 0.06)
    user_B = UserState("B", 0.9, 0.05, 0.15, 0.06)
    user_C = UserState("C", 0.9, 0.05, 0.2, 0.06)

    protocol.read_neural_phase_space(user_self, user_B, user_C)

    action = protocol.apply_calibration_loop()

    assert protocol.buffer.delta_theta > 0
    assert action == "PROCEED_TO_SEAL"


def test_lattice_protocol_collaborative():
    metrics = LatticeMetrics()
    protocol = TriangularLatticeProtocol(metrics)
    protocol.initialize_ledger_buffer(("A", "B", "C"))

    user_self = UserState("A", 0.95, 0.05, 0.1, 0.08)
    user_B = UserState("B", 0.96, 0.06, 0.2, 0.08)

    # Needs a dummy for user_C in this buffer
    user_C = UserState("C", 0.95, 0.05, 0.15, 0.08)

    collab_space = CollaborativeSpace(user_self, user_B)

    protocol.read_neural_phase_space(user_self, user_B, user_C, collab_space)

    action = protocol.apply_calibration_loop(user_self, user_B, collab_space)

    assert action == "PROCEED_TO_SEAL"


def test_lattice_protocol_collision():
    metrics = LatticeMetrics()
    protocol = TriangularLatticeProtocol(metrics)
    protocol.initialize_ledger_buffer(("A", "B", "C"))

    # Same phase means collision
    user_self = UserState("A", 0.95, 0.05, 0.1, 0.08)
    user_B = UserState("B", 0.96, 0.06, 0.1, 0.08)
    user_C = UserState("C", 0.95, 0.05, 0.1, 0.08)

    collab_space = CollaborativeSpace(user_self, user_B)

    protocol.read_neural_phase_space(user_self, user_B, user_C, collab_space)

    action = protocol.apply_calibration_loop(user_self, user_B, collab_space)

    assert action == "HOLD_FOR_ORTHOGONALITY"
