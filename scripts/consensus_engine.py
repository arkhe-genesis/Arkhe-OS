# ============================================================================
# ARKHE OS v∞.Ω.∇+++.14.1 — Proof-of-Coherence Consensus Engine
# Purpose: Cryptographic voting for temporal fork merging with Odysseus bonus
#          Extended to multi-dimensional ε (phase, latency, power coherence)
# ============================================================================

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import numpy as np
import hashlib
import time

@dataclass
class CoherenceStake:
    """Historical multi-dimensional ε-preservation fidelity of a vertex."""
    vertex_did: str
    epsilon_history: np.ndarray  # ε values over last T logical timestamps, shape (T, 3) for (phase, latency, power)
    target_epsilon: np.ndarray = field(default_factory=lambda: np.array([0.07, 0.07, 0.07]))
    sigma: np.ndarray = field(default_factory=lambda: np.array([0.015, 0.015, 0.015]))

    @property
    def stake_value(self) -> float:
        """Exponential decay from target ε across all dimensions."""
        # Calculate squared distance weighted by sigma for each dimension
        diff_sq = (self.epsilon_history - self.target_epsilon)**2
        decay_components = diff_sq / (2 * self.sigma**2)
        # Sum across dimensions to get multivariate Gaussian exponent
        decay_sum = np.sum(decay_components, axis=1)
        return float(np.mean(np.exp(-decay_sum)))

@dataclass
class ForkVote:
    """Signed vote for/against fork merge."""
    voter_did: str
    vote_direction: bool  # True=for merge, False=against
    timestamp: float
    signature: bytes      # Cryptographic signature of (fork_id + vote_direction + ts)
    weight: float = 0.0   # Computed by consensus engine

class ProofOfCoherenceConsensus:
    """
    Implements PoC voting + Odysseus super-linear bonus for temporal fork resolution.
    Extended for multi-dimensional ε.
    """
    def __init__(self, consensus_threshold: float = 0.55, odysseus_multiplier: float = 0.3):
        self.threshold = consensus_threshold
        self.odys_mult = odysseus_multiplier
        self.stakes: Dict[str, CoherenceStake] = {}
        self.votes: Dict[str, List[ForkVote]] = {}

    def register_vertex(self, stake: CoherenceStake) -> None:
        self.stakes[stake.vertex_did] = stake

    def cast_vote(self, fork_id: str, vote: ForkVote, epsilon_fork: np.ndarray) -> None:
        """Weight vote by voter's coherence stake and fork's multi-dimensional ε proximity."""
        if vote.voter_did not in self.stakes:
            raise ValueError("Unregistered vertex")

        stake = self.stakes[vote.voter_did]
        # Weight = stake × fork coherence alignment
        diff_sq = (epsilon_fork - stake.target_epsilon)**2
        decay_components = diff_sq / (2 * stake.sigma**2)
        fork_alignment = np.exp(-np.sum(decay_components))

        vote.weight = stake.stake_value * fork_alignment

        if fork_id not in self.votes:
            self.votes[fork_id] = []
        self.votes[fork_id].append(vote)

    def evaluate_merge(self, fork_id: str, odysseus_insight_ratio: float = 1.0) -> Tuple[bool, float]:
        """
        Compute weighted consensus + Odysseus bonus.
        Returns (accept_merge, consensus_score)
        """
        if fork_id not in self.votes:
            return False, 0.0

        for_votes = sum(v.weight for v in self.votes[fork_id] if v.vote_direction)
        against_votes = sum(v.weight for v in self.votes[fork_id] if not v.vote_direction)

        # Odysseus super-linear bonus
        odys_bonus = max(0.0, odysseus_insight_ratio - 1.0) * self.odys_mult * (for_votes + against_votes)

        total_weight = for_votes + against_votes + odys_bonus
        consensus_score = for_votes / max(total_weight, 1e-9)

        accept = consensus_score >= self.threshold
        return accept, consensus_score

    def reset_fork(self, fork_id: str) -> None:
        self.votes.pop(fork_id, None)
