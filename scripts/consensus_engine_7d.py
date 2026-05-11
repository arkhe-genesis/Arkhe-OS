# ============================================================================
# ARKHE OS v∞.Ω.∇+++.14.3 — Seven-Dimensional Proof-of-Coherence Consensus
# Dimensions: [phase, latency, power, mercy_gap, security, privacy, interpretability]
# ============================================================================

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import numpy as np
from numpy.linalg import inv, eigvalsh

@dataclass
class CoherenceTensor7D:
    """7D coherence state for cathedral operations."""
    phase: float           # ε_φ ∈ [0, 1]
    latency_us: float      # ε_τ ∈ [400, 600] µs
    power_mw: float        # ε_ρ ∈ [120, 180] mW
    mercy_gap: float       # ε_ε ∈ [0, 1]
    security: float        # ε_σ ∈ [0, 1] (crypto integrity score)
    privacy: float         # ε_π ∈ [0, 1] (ZK/consent adherence)
    interpretability: float # ε_ι ∈ [0, 1] (symbolic annotation quality)

    def to_vector(self) -> np.ndarray:
        return np.array([
            self.phase, self.latency_us, self.power_mw,
            self.mercy_gap, self.security, self.privacy, self.interpretability
        ])

    @staticmethod
    def target() -> 'CoherenceTensor7D':
        return CoherenceTensor7D(
            phase=0.07, latency_us=500.0, power_mw=150.0, mercy_gap=0.07,
            security=0.95, privacy=0.92, interpretability=0.88
        )

    @staticmethod
    def hard_bounds() -> Tuple[np.ndarray, np.ndarray]:
        """Hard safety bounds for infinity-norm check."""
        lower = np.array([0.04, 400.0, 120.0, 0.04, 0.90, 0.85, 0.80])
        upper = np.array([0.10, 600.0, 180.0, 0.10, 1.00, 1.00, 1.00])
        return lower, upper

    @staticmethod
    def soft_targets() -> np.ndarray:
        """Preferred targets for Mahalanobis scoring."""
        return CoherenceTensor7D.target().to_vector()

    @staticmethod
    def nominal_stds() -> np.ndarray:
        """Nominal standard deviations for each dimension."""
        return np.array([0.015, 30.0, 15.0, 0.015, 0.025, 0.035, 0.040])

@dataclass
class CoherenceStake7D:
    """7D coherence stake with full covariance modeling."""
    vertex_did: str
    coherence_history: List[CoherenceTensor7D]
    covariance: Optional[np.ndarray] = None

    def __post_init__(self):
        if self.covariance is None:
            # Default covariance with key engineering couplings
            stds = CoherenceTensor7D.nominal_stds()
            self.covariance = np.diag(stds**2)
            # Add critical couplings
            self.covariance[1, 2] = self.covariance[2, 1] = 0.6 * stds[1] * stds[2]  # latency-power
            self.covariance[4, 5] = self.covariance[5, 4] = 0.4 * stds[4] * stds[5]  # security-privacy
            self.covariance[0, 6] = self.covariance[6, 0] = -0.3 * stds[0] * stds[6]  # phase-interpretability

    @property
    def stake_value(self) -> float:
        """Mahalanobis-based 7D coherence fidelity."""
        if not self.coherence_history:
            return 0.0
        target = CoherenceTensor7D.soft_targets()
        cov_inv = inv(self.covariance)

        scores = []
        for ct in self.coherence_history:
            diff = ct.to_vector() - target
            mahal = diff @ cov_inv @ diff
            # Ensure numerical stability
            if mahal > 100:  # Extreme deviation
                scores.append(1e-6)
            else:
                scores.append(np.exp(-0.5 * mahal))
        return float(np.mean(scores))

@dataclass
class ForkVote7D:
    """Signed vote with 7D coherence assessment."""
    voter_did: str
    vote_direction: bool
    timestamp: float
    signature: bytes
    fork_coherence: CoherenceTensor7D
    weight: float = 0.0

class ProofOfCoherenceConsensus7D:
    """
    Seven-dimensional PoC consensus with full covariance modeling,
    harmonic Odysseus bonus, and hard safety bounds.
    """

    def __init__(
        self,
        consensus_threshold: float = 0.55,
        odysseus_multiplier: float = 0.3,
        harmonic_penalty_factor: float = 2.0
    ):
        self.threshold = consensus_threshold
        self.odys_mult = odysseus_multiplier
        self.harmonic_factor = harmonic_penalty_factor
        self.stakes: Dict[str, CoherenceStake7D] = {}
        self.votes: Dict[str, List[ForkVote7D]] = {}
        # Global covariance for vote weighting
        stds = CoherenceTensor7D.nominal_stds()
        self.covariance_global = np.diag(stds**2)
        self.covariance_global[1, 2] = self.covariance_global[2, 1] = 0.6 * stds[1] * stds[2]
        self.covariance_global[4, 5] = self.covariance_global[5, 4] = 0.4 * stds[4] * stds[5]
        self.covariance_global[0, 6] = self.covariance_global[6, 0] = -0.3 * stds[0] * stds[6]

    def register_vertex(self, stake: CoherenceStake7D) -> None:
        self.stakes[stake.vertex_did] = stake

    def cast_vote(self, fork_id: str, vote: ForkVote7D) -> None:
        """Weight vote by 7D Mahalanobis alignment."""
        if vote.voter_did not in self.stakes:
            raise ValueError("Unregistered vertex")

        stake = self.stakes[vote.voter_did]
        target = CoherenceTensor7D.soft_targets()
        fork_vec = vote.fork_coherence.to_vector()

        cov_inv = inv(self.covariance_global)
        diff = fork_vec - target
        mahal = diff @ cov_inv @ diff
        alignment = np.exp(-0.5 * mahal) if mahal < 100 else 1e-6

        vote.weight = stake.stake_value * alignment

        if fork_id not in self.votes:
            self.votes[fork_id] = []
        self.votes[fork_id].append(vote)

    def evaluate_merge(
        self,
        fork_id: str,
        odysseus_insight_ratio: float = 1.0,
        fork_coherence: Optional[CoherenceTensor7D] = None
    ) -> Tuple[bool, float, Dict[str, float], Optional[str]]:
        """
        Compute 7D consensus with hard safety checks.
        Returns: (accept, consensus_score, dim_scores, rejection_reason)
        """
        if fork_id not in self.votes:
            return False, 0.0, {}, "no_votes"

        # Hard safety check: infinity-norm bounds
        if fork_coherence:
            lower, upper = CoherenceTensor7D.hard_bounds()
            fork_vec = fork_coherence.to_vector()
            if np.any(fork_vec < lower) or np.any(fork_vec > upper):
                violators = [
                    dim for dim, val, lo, hi in zip(
                        ["phase", "latency", "power", "mercy", "security", "privacy", "interpretability"],
                        fork_vec, lower, upper
                    ) if val < lo or val > hi
                ]
                return False, 0.0, {}, f"hard_bounds_violated:{','.join(violators)}"

        # Weighted vote aggregation
        for_votes = sum(v.weight for v in self.votes[fork_id] if v.vote_direction)
        against_votes = sum(v.weight for v in self.votes[fork_id] if not v.vote_direction)

        # Odysseus bonus with harmonic penalty for dimensional imbalance
        if fork_coherence:
            cov_inv = inv(self.covariance_global)
            diff = fork_coherence.to_vector() - CoherenceTensor7D.soft_targets()
            mahal = diff @ cov_inv @ diff
            coherence_penalty = np.exp(-0.5 * mahal) if mahal < 100 else 1e-6

            # Harmonic mean penalty: bonus reduced if any dimension is weak
            dim_scores = [
                np.exp(-(fork_coherence.phase - 0.07)**2 / (2*0.015**2)),
                np.exp(-(fork_coherence.latency_us - 500)**2 / (2*30**2)),
                np.exp(-(fork_coherence.power_mw - 150)**2 / (2*15**2)),
                np.exp(-(fork_coherence.mercy_gap - 0.07)**2 / (2*0.015**2)),
                np.exp(-(fork_coherence.security - 0.95)**2 / (2*0.025**2)),
                np.exp(-(fork_coherence.privacy - 0.92)**2 / (2*0.035**2)),
                np.exp(-(fork_coherence.interpretability - 0.88)**2 / (2*0.040**2))
            ]
            harmonic_mean = 7.0 / sum(1.0 / max(s, 1e-6) for s in dim_scores)
            harmonic_penalty = 1.0 / (1.0 + self.harmonic_factor * (1.0 - harmonic_mean))
        else:
            coherence_penalty = 1.0
            harmonic_penalty = 1.0
            dim_scores = {}

        odys_bonus = (
            max(0.0, odysseus_insight_ratio - 1.0) *
            self.odys_mult *
            (for_votes + against_votes) *
            coherence_penalty *
            harmonic_penalty
        )

        total_weight = for_votes + against_votes + odys_bonus
        consensus_score = for_votes / max(total_weight, 1e-9)

        accept = consensus_score >= self.threshold
        return accept, consensus_score, dim_scores, None

    def reset_fork(self, fork_id: str) -> None:
        self.votes.pop(fork_id, None)
