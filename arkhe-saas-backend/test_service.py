#!/usr/bin/env .venv/bin/python
"""Test script for Arkhe PoC SaaS backend."""
import sys
sys.path.insert(0, '.')

from services.consensus_service import ConsensusService, ServiceCoherenceStake
import numpy as np


def test_stake_computation():
    stake = ServiceCoherenceStake(
        vertex_did='test_vertex',
        epsilon_history=np.array([[0.07, 0.07, 0.07] for _ in range(10)]),
        target_epsilon=np.array([0.07, 0.07, 0.07]),
        sigma=np.array([0.015, 0.015, 0.015]),
    )
    assert abs(stake.stake_value - 1.0) < 0.001, f"Expected stake ~1.0, got {stake.stake_value}"
    print(f"✓ Stake computation: {stake.stake_value:.4f}")


def test_consensus_service():
    service = ConsensusService()
    network_id = 'test_net'
    epsilon_history = [[0.07, 0.07, 0.07] for _ in range(10)]

    # Register vertices
    for i in range(5):
        sv = service.register_vertex(
            network_id=network_id,
            vertex_did=f'did:arkhe:node_{i}',
            epsilon_history=epsilon_history,
            target_epsilon=[0.07, 0.07, 0.07],
            sigma=[0.015, 0.015, 0.015],
        )
        assert sv > 0, f"Stake value should be positive, got {sv}"
    print(f"✓ Registered 5 vertices")

    # Cast votes
    for i in range(5):
        w = service.cast_vote(
            network_id=network_id,
            fork_id='fork_test',
            voter_did=f'did:arkhe:node_{i}',
            vote_direction=(i % 2 == 0),
            timestamp=0.0,
            signature='SIG',
            epsilon_fork=[0.07, 0.07, 0.07],
        )
        assert w > 0, f"Weight should be positive, got {w}"
    print(f"✓ Cast 5 votes (3 for, 2 against)")

    # Evaluate merge
    accept, score, for_w, against_w, total = service.evaluate_merge(
        network_id=network_id,
        fork_id='fork_test',
        odysseus_insight_ratio=1.1,
    )
    print(f"✓ Consensus: accept={accept}, score={score:.4f}, for={for_w:.2f}, against={against_w:.2f}")
    assert accept, "Should accept (3 for votes should exceed threshold)"
    assert total == 5, f"Expected 5 votes, got {total}"


if __name__ == '__main__':
    test_stake_computation()
    test_consensus_service()
    print('\n✅ All tests passed!')