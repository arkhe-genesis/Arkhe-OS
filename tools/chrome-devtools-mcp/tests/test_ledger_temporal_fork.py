import pytest
from core.protocol.fork.ledger_temporal_fork_protocol import LedgerTemporalForkProtocol, LedgerState

def setup_protocol():
    protocol = LedgerTemporalForkProtocol(main_chain_root=b"test_root", consensus_threshold=0.03)

    # Initialize some states
    for i in range(1, 4):
        state = LedgerState(
            logical_timestamp=float(i),
            merkle_root=f"root_{i}".encode(),
            face_hashes=[f"face_{i}".encode()],
            vertex_signatures={"v1": b"sig", "v2": b"sig"},
            epsilon_stats={"mean": 0.08}, # Slightly off from target 0.07
        )
        protocol.main_chain[float(i)] = state

    return protocol

def test_fork_creation():
    protocol = setup_protocol()

    fork_id = protocol.fork_at(2.0, "test_fork")
    assert fork_id in protocol.forks

    # Fork history should contain ts 1.0 and 2.0, but not 3.0
    fork_history = protocol.forks[fork_id]
    assert 1.0 in fork_history
    assert 2.0 in fork_history
    assert 3.0 not in fork_history

def test_append_to_fork():
    protocol = setup_protocol()
    fork_id = protocol.fork_at(2.0)

    new_state = LedgerState(
        logical_timestamp=3.5,
        merkle_root=b"fork_root_3.5",
        face_hashes=[],
        vertex_signatures={"v1": b"sig", "v2": b"sig"},
        epsilon_stats={"mean": 0.07}
    )

    protocol.append_to_fork(fork_id, new_state)
    assert 3.5 in protocol.forks[fork_id]
    assert protocol.forks[fork_id][3.5].epsilon_stats["mean"] == 0.07

def test_evaluate_fork_coherence():
    protocol = setup_protocol()
    fork_id = protocol.fork_at(2.0)

    # Main chain tip is at 3.0 with epsilon 0.08
    # Fork tip will be at 4.0 with epsilon 0.07 (perfect) and odysseus bonus
    new_state = LedgerState(
        logical_timestamp=4.0,
        merkle_root=b"fork_root_4",
        face_hashes=[],
        vertex_signatures={"v1": b"sig", "v2": b"sig"},
        epsilon_stats={"mean": 0.07},
        odysseus_insight=0.5
    )
    protocol.append_to_fork(fork_id, new_state)

    coherence_gain = protocol.evaluate_fork_coherence(fork_id)
    # The fork has better epsilon (closer to 0.07) and odysseus bonus
    # Expected behavior is a positive coherence gain > consensus_threshold
    assert coherence_gain > protocol.consensus_threshold

def test_merge_fork_success():
    protocol = setup_protocol()
    fork_id = protocol.fork_at(2.0)

    new_state = LedgerState(
        logical_timestamp=4.0,
        merkle_root=b"fork_root_4",
        face_hashes=[],
        vertex_signatures={"v1": b"sig", "v2": b"sig"},
        epsilon_stats={"mean": 0.07},
        odysseus_insight=0.5
    )
    protocol.append_to_fork(fork_id, new_state)

    assert protocol.merge_fork(fork_id) is True
    # Fork should be deleted
    assert fork_id not in protocol.forks
    # Main chain should now have the fork tip
    assert 4.0 in protocol.main_chain
    # Main chain should NOT have the original 3.0 because it diverged at 2.0
    assert 3.0 not in protocol.main_chain

def test_merge_fork_rejection():
    protocol = setup_protocol()
    fork_id = protocol.fork_at(2.0)

    # Fork tip with worse epsilon and no bonus
    new_state = LedgerState(
        logical_timestamp=4.0,
        merkle_root=b"fork_root_4",
        face_hashes=[],
        vertex_signatures={"v1": b"sig", "v2": b"sig"},
        epsilon_stats={"mean": 0.15},
        odysseus_insight=0.0
    )
    protocol.append_to_fork(fork_id, new_state)

    assert protocol.merge_fork(fork_id) is False
    # Fork should still exist
    assert fork_id in protocol.forks

def test_rollback():
    protocol = setup_protocol()

    protocol.rollback_to(2.0)

    assert 1.0 in protocol.main_chain
    assert 2.0 in protocol.main_chain
    assert 3.0 not in protocol.main_chain
