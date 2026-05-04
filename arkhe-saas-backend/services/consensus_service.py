# arkhe-saas-backend/services/consensus_service.py
"""PoC consensus service wrapping consensus_engine.py."""
from typing import Dict, List, Tuple

import numpy as np

from dataclasses import dataclass, field


# ─── Inline fallback engine (mirrors consensus_engine.py logic) ─────────────────

@dataclass
class ServiceCoherenceStake:
    """Aligned with consensus_engine.CoherenceStake."""
    vertex_did: str
    epsilon_history: np.ndarray
    target_epsilon: np.ndarray = field(default_factory=lambda: np.array([0.07, 0.07, 0.07]))
    sigma: np.ndarray = field(default_factory=lambda: np.array([0.015, 0.015, 0.015]))

    @property
    def stake_value(self) -> float:
        diff_sq = (self.epsilon_history - self.target_epsilon) ** 2
        decay_components = diff_sq / (2 * self.sigma ** 2)
        decay_sum = np.sum(decay_components, axis=1)
        return float(np.mean(np.exp(-decay_sum)))


@dataclass
class ServiceForkVote:
    voter_did: str
    vote_direction: bool
    timestamp: float
    signature: str
    weight: float = 0.0


class InlineConsensusEngine:
    """Fallback engine when consensus_engine.py is unavailable."""

    def __init__(self, consensus_threshold: float = 0.55, odysseus_multiplier: float = 0.3):
        self.threshold = consensus_threshold
        self.odys_mult = odysseus_multiplier
        self.stakes: Dict[str, ServiceCoherenceStake] = {}
        self.votes: Dict[str, List[ServiceForkVote]] = {}

    def register_vertex(self, stake: ServiceCoherenceStake) -> None:
        self.stakes[stake.vertex_did] = stake

    def cast_vote(self, fork_id: str, vote: ServiceForkVote, epsilon_fork: np.ndarray) -> None:
        if vote.voter_did not in self.stakes:
            raise ValueError("Unregistered vertex")
        stake = self.stakes[vote.voter_did]
        diff_sq = (epsilon_fork - stake.target_epsilon) ** 2
        decay_components = diff_sq / (2 * stake.sigma ** 2)
        fork_alignment = np.exp(-np.sum(decay_components))
        vote.weight = stake.stake_value * fork_alignment
        if fork_id not in self.votes:
            self.votes[fork_id] = []
        self.votes[fork_id].append(vote)

    def evaluate_merge(self, fork_id: str, odysseus_insight_ratio: float = 1.0):
        if fork_id not in self.votes:
            return False, 0.0
        for_votes = sum(v.weight for v in self.votes[fork_id] if v.vote_direction)
        against_votes = sum(v.weight for v in self.votes[fork_id] if not v.vote_direction)
        odys_bonus = max(0.0, odysseus_insight_ratio - 1.0) * self.odys_mult * (for_votes + against_votes)
        total_weight = for_votes + against_votes + odys_bonus
        consensus_score = for_votes / max(total_weight, 1e-9)
        accept = consensus_score >= self.threshold
        return accept, consensus_score

    def reset_fork(self, fork_id: str) -> None:
        self.votes.pop(fork_id, None)


# ─── Consensus service ─────────────────────────────────────────────────────────

class ConsensusService:
    """
    Multi-tenant PoC consensus service.
    Wraps the logic from consensus_engine.py with database persistence.
    """

    def __init__(self):
        self._stakes: Dict[str, Dict[str, ServiceCoherenceStake]] = {}
        self._votes: Dict[str, List[ServiceForkVote]] = {}

    def register_vertex(
        self,
        network_id: str,
        vertex_did: str,
        epsilon_history: List[List[float]],
        target_epsilon: List[float],
        sigma: List[float],
        threshold: float = 0.55,
        odys_mult: float = 0.3,
    ) -> float:
        """Register a vertex and compute its stake value."""
        if network_id not in self._stakes:
            self._stakes[network_id] = {}

        stake = ServiceCoherenceStake(
            vertex_did=vertex_did,
            epsilon_history=np.array(epsilon_history),
            target_epsilon=np.array(target_epsilon),
            sigma=np.array(sigma),
        )
        self._stakes[network_id][vertex_did] = stake
        return stake.stake_value

    def cast_vote(
        self,
        network_id: str,
        fork_id: str,
        voter_did: str,
        vote_direction: bool,
        timestamp: float,
        signature: str,
        epsilon_fork: List[float],
        threshold: float = 0.55,
        odys_mult: float = 0.3,
    ) -> float:
        """Cast a vote weighted by coherence stake."""
        if network_id not in self._stakes:
            self._stakes[network_id] = {}
        if network_id not in self._votes:
            self._votes[network_id] = []

        stake = self._stakes[network_id].get(voter_did)
        if stake is None:
            stake = ServiceCoherenceStake(
                vertex_did=voter_did,
                epsilon_history=np.array([[0.07, 0.07, 0.07] for _ in range(10)]),
                target_epsilon=np.array([0.07, 0.07, 0.07]),
                sigma=np.array([0.015, 0.015, 0.015]),
            )
            self._stakes[network_id][voter_did] = stake

        diff_sq = (np.array(epsilon_fork) - stake.target_epsilon) ** 2
        decay_components = diff_sq / (2 * stake.sigma ** 2)
        fork_alignment = np.exp(-np.sum(decay_components))
        weight = stake.stake_value * fork_alignment

        vote = ServiceForkVote(
            voter_did=voter_did,
            vote_direction=vote_direction,
            timestamp=timestamp,
            signature=signature,
            weight=weight,
        )
        self._votes[network_id].append(vote)
        return weight

    def evaluate_merge(
        self,
        network_id: str,
        fork_id: str,
        odysseus_insight_ratio: float = 1.0,
        threshold: float = 0.55,
        odys_mult: float = 0.3,
    ) -> Tuple[bool, float, float, float, int]:
        """
        Evaluate consensus for a fork merge.
        Returns (accept, consensus_score, for_weight, against_weight, total_votes)
        """
        votes_all = self._votes.get(network_id, [])

        for_votes = sum(v.weight for v in votes_all if v.vote_direction)
        against_votes = sum(v.weight for v in votes_all if not v.vote_direction)

        odys_bonus = max(0.0, odysseus_insight_ratio - 1.0) * odys_mult * (for_votes + against_votes)
        total_weight = for_votes + against_votes + odys_bonus
        consensus_score = for_votes / max(total_weight, 1e-9)

        accept = consensus_score >= threshold
        return accept, consensus_score, for_votes, against_votes, len(votes_all)

    def reset_fork(self, network_id: str) -> None:
        self._votes[network_id] = []


# Singleton instance
consensus_service = ConsensusService()