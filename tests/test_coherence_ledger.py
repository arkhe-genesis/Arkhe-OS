import pytest
from core.ledger.coherence_ledger import CoherenceLedgerEntry, FaceBuffer, LatticeMetrics
from core.neuro.pac_neuromapping import calibrate_neurodynamic_pac, validate_excess_margin
from core.protocol.triangular_lattice_protocol import TriangularLatticeProtocol
from core.lattice.orthogonal_witness import UserState

def test_validate_equilateral():
    # Valid face
    entry = CoherenceLedgerEntry(
        face_id="test_face_1",
        vertices=("A", "B", "C"),
        edges=(0.05, 0.06, 0.07),
        ceremonial_amplitude=0.08,
        excess_tolerance=0.0472,
        stability_metric=0.07,
        face_state="SEALED",
        ritual_phase="SEAL",
        timestamp_utc="2024-01-01T00:00:00Z",
        witness_signatures=["sig1", "sig2", "sig3"],
        prev_hash="0"*64
    )
    assert entry.validate_equilateral() is True

    # Invalid face (Δθ > 0.10)
    entry.stability_metric = 0.11
    assert entry.validate_equilateral() is False
    entry.stability_metric = 0.07

    # Invalid face (ε < 0.04)
    entry.excess_tolerance = 0.03
    assert entry.validate_equilateral() is False
    entry.excess_tolerance = 0.0472

    # Invalid face (edge < 0.04)
    entry.edges = (0.03, 0.06, 0.07)
    assert entry.validate_equilateral() is False

def test_calibrate_pac():
    # Inside margin, no adjustment
    assert calibrate_neurodynamic_pac(0.08, 0.05) == 0.0

    # Needs increase, limited to 0.01
    assert round(calibrate_neurodynamic_pac(0.20, 0.05), 3) == 0.01
    assert round(calibrate_neurodynamic_pac(0.10, 0.05), 3) == 0.005

    # Needs decrease, limited to -0.01
    assert round(calibrate_neurodynamic_pac(0.05, 0.20), 3) == -0.01
    assert round(calibrate_neurodynamic_pac(0.05, 0.10), 3) == -0.005

def test_validate_excess_margin():
    assert validate_excess_margin(0.0472) is True
    assert validate_excess_margin(0.03) is False
    assert validate_excess_margin(0.11) is False

def test_triangular_lattice_protocol():
    metrics = LatticeMetrics()
    protocol = TriangularLatticeProtocol(metrics)

    # Initialize
    protocol.initialize_ledger_buffer(vertices=("V1", "V2", "V3"))
    assert protocol.buffer is not None
    assert protocol.buffer.state == "FORMING"

    # Read Neural Phase Space (Valid bounds)
    # Give it values that make edge differences:
    # ab = abs(0.1 - 0.05) = 0.05
    # bc = abs(0.15 - 0.1) = 0.05
    # ca = abs(0.05 - 0.15) = 0.10
    protocol.read_neural_phase_space(
        user_self=UserState("V1", 0.9, 0.05, 0.05, 0.08),
        user_A=UserState("V2", 0.9, 0.05, 0.1, 0.08),
        user_B=UserState("V3", 0.9, 0.05, 0.15, 0.08),
    )

    assert round(protocol.buffer.delta_theta, 2) == 0.10
    assert protocol.buffer.k == 0.08
    assert protocol.buffer.epsilon == 0.05

    # Calibration Loop
    action = protocol.apply_calibration_loop()
    assert action == "PROCEED_TO_SEAL"
    assert protocol.buffer.ritual_phase == "SEAL"

    # Seal & Record
    entry = protocol.seal_and_record()
    assert entry is not None
    assert entry.face_state == "SEALED"
    assert len(entry.witness_signatures) == 3
    assert metrics.total_faces == 1
    assert len(metrics.ledger) == 1

def test_triangular_lattice_protocol_calibration_adjustments():
    metrics = LatticeMetrics()
    protocol = TriangularLatticeProtocol(metrics)
    protocol.initialize_ledger_buffer(vertices=("V1", "V2", "V3"))

    # Test Pause (delta_theta > 0.15)
    protocol.read_neural_phase_space(
        user_self=UserState("V1", 0.9, 0.0, 0.05, 0.08),
        user_A=UserState("V2", 0.9, 0.05, 0.2, 0.08),
        user_B=UserState("V3", 0.9, 0.05, 0.1, 0.08),
    )
    assert protocol.apply_calibration_loop() == "PAUSE"

    # Test Increase K (epsilon < 0.04)
    protocol.read_neural_phase_space(
        user_self=UserState("V1", 0.9, 0.03, 0.05, 0.08),
        user_A=UserState("V2", 0.9, 0.05, 0.1, 0.08),
        user_B=UserState("V3", 0.9, 0.05, 0.1, 0.08),
    )
    assert protocol.apply_calibration_loop() == "INCREASE_K"
    assert round(protocol.buffer.k, 3) == 0.09

    # Test Decrease K (epsilon > 0.10)
    protocol.read_neural_phase_space(
        user_self=UserState("V1", 0.9, 0.15, 0.05, 0.08),
        user_A=UserState("V2", 0.9, 0.15, 0.1, 0.08),
        user_B=UserState("V3", 0.9, 0.05, 0.15, 0.08),
    )
    assert protocol.apply_calibration_loop() == "DECREASE_K"
    assert round(protocol.buffer.k, 3) == 0.07
