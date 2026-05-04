import pytest
import time
import hashlib
from core.protocol.crfl_engine import PhaseAlignedStateVector, ConflictFreeReplicatedLattice

def generate_mock_pasv(participant_id: str, theta: float, pdi: float, epsilon: float, device_id: str) -> PhaseAlignedStateVector:
    pasv = PhaseAlignedStateVector(
        theta_normalized=theta,
        pdi_normalized=pdi,
        epsilon_normalized=epsilon,
        phase_cycle_index=1,
        relative_timestamp=10.5,
        platform_id=device_id,
        sampling_rate_hz=256,
        latency_estimate_ms=15.0,
        phase_variance_window=0.05,
        mercy_gap_integrity=0.95,
        state_hash="",
        prev_state_hash="prev_hash_stub"
    )

    # Compute valid hash
    expected_hash = hashlib.sha256(
        f"{pasv.theta_normalized}:{pasv.pdi_normalized}:{pasv.epsilon_normalized}:"
        f"{pasv.phase_cycle_index}:{pasv.relative_timestamp}:"
        f"{pasv.platform_id}:{pasv.sampling_rate_hz}:{pasv.latency_estimate_ms}:"
        f"{pasv.phase_variance_window}:{pasv.mercy_gap_integrity}:"
        f"{pasv.prev_state_hash}:{participant_id}".encode()
    ).hexdigest()

    pasv.state_hash = expected_hash
    return pasv

def test_is_orthogonal_compatible():
    pasv1 = generate_mock_pasv("participant_1", 0.1, 0.9, 0.05, "device_A")
    pasv2 = generate_mock_pasv("participant_1", 0.2, 0.9, 0.06, "device_B")

    # Valid orthogonality (diff = 0.1, which is between 0.03 and 0.15)
    assert pasv1.is_orthogonal_compatible(pasv2) is True

    # Invalid: Too close (phase collision)
    pasv3 = generate_mock_pasv("participant_1", 0.11, 0.9, 0.05, "device_C")
    assert pasv1.is_orthogonal_compatible(pasv3) is False

    # Invalid: Too far (drift)
    pasv4 = generate_mock_pasv("participant_1", 0.5, 0.9, 0.05, "device_D")
    assert pasv1.is_orthogonal_compatible(pasv4) is False

    # Invalid: PDI mismatch
    pasv5 = generate_mock_pasv("participant_1", 0.2, 0.5, 0.06, "device_E")
    assert pasv1.is_orthogonal_compatible(pasv5) is False

def test_crfl_engine_merge():
    engine = ConflictFreeReplicatedLattice("participant_1")

    pasv_A = generate_mock_pasv("participant_1", 0.1, 0.9, 0.05, "device_A")
    pasv_B = generate_mock_pasv("participant_1", 0.2, 0.9, 0.06, "device_B")

    # First device sends data, no merge yet
    face1 = engine.receive_state_vector("device_A", pasv_A)
    assert face1 is None

    # Second device sends data, orthogonal merge successful
    face2 = engine.receive_state_vector("device_B", pasv_B)
    assert face2 is not None
    assert face2.participant_a == "participant_1"
    assert face2.participant_b == "device_A"
    assert face2.collaborative_space.epsilon_inter == 0.055
    assert len(engine.lattice_faces) == 1
