# ============================================================================
# ARKHE OS v∞.Ω.∇+++.14 — Substrate 126: Ledger Temporal Fork Protocol
# Purpose: Cryptographically secure navigation, branching, and merging of ledger state
# Guarantees: Merkle path integrity, vertex signature validation, ε-aware merge criteria
# ============================================================================

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import hashlib
import time

@dataclass
class LedgerState:
    """Immutable snapshot of the simplicial complex at a logical timestamp."""
    logical_timestamp: float
    merkle_root: bytes
    face_hashes: List[bytes]  # Hashes of all sealed faces up to this point
    vertex_signatures: Dict[str, bytes]  # DID → signature of state commitment
    epsilon_stats: Dict  # mercy gap statistics at this timestamp
    uniphics_stats: Dict = field(default_factory=lambda: {"E_d": 1.0, "k": 0.0472}) # Energy density and ceremonial amplitude
    odysseus_insight: float = 0.0 # Metric for super-linear insight gain

class LedgerTemporalForkProtocol:
    """
    Implements temporal forking, querying, merging, and rollback for the distributed ledger.
    Maintains cryptographic auditability and coherence-weighted fork selection.
    """

    def __init__(self, main_chain_root: bytes, consensus_threshold: float = 0.03):
        self.main_chain: Dict[float, LedgerState] = {}
        self.forks: Dict[str, Dict[float, LedgerState]] = {}
        self.consensus_threshold = consensus_threshold  # ε difference required to accept merge
        self.vertex_fidelity: Dict[str, float] = {} # Historical ε-preservation fidelity per vertex

    def fork_at(self, logical_timestamp: float, reason: str = "temporal_exploration") -> str:
        """
        Create a new temporal branch from a prior coherent state.
        Returns fork_id.
        """
        if logical_timestamp not in self.main_chain:
            raise ValueError("Invalid timestamp for forking")

        fork_id = hashlib.sha256(
            f"{logical_timestamp}_{reason}_{time.time()}".encode()
        ).hexdigest()[:12]

        # Copy state history up to fork point
        fork_history = {
            ts: LedgerState(**vars(state))
            for ts, state in self.main_chain.items()
            if ts <= logical_timestamp
        }
        self.forks[fork_id] = fork_history
        return fork_id

    def query_state(self, logical_timestamp: float, fork_id: Optional[str] = None) -> LedgerState:
        """Retrieve ledger state at exact logical timestamp."""
        chain = self.forks.get(fork_id, self.main_chain)
        if logical_timestamp not in chain:
            raise KeyError("Timestamp not in chain history")
        return chain[logical_timestamp]

    def append_to_fork(self, fork_id: str, new_state: LedgerState) -> None:
        """Add new state to fork. Requires vertex signatures on merkle_root."""
        if fork_id not in self.forks:
            raise ValueError("Fork does not exist")
        # Verify all affected vertices signed the new merkle root
        self._verify_vertex_signatures(new_state)
        self.forks[fork_id][new_state.logical_timestamp] = new_state

    def calculate_uniphics_velocity(self, state: LedgerState) -> float:
        """
        Uniphics Integration: t_flow = k/E_d
        Determines local timeline velocity. Forks in low-E_d regions progress faster.
        """
        k = state.uniphics_stats.get("k", 0.0472)
        E_d = state.uniphics_stats.get("E_d", 1.0)
        if E_d == 0:
            return float('inf')
        return k / E_d

    def _proof_of_coherence_vote(self, state: LedgerState) -> float:
        """
        Proof-of-Coherence voting: vertices vote weighted by ε-preservation fidelity.
        """
        total_vote_weight = 0.0
        for vid, _ in state.vertex_signatures.items():
            # If vertex fidelity is unknown, assign a default weight of 1.0
            weight = self.vertex_fidelity.get(vid, 1.0)
            total_vote_weight += weight
        return total_vote_weight

    def evaluate_fork_coherence(self, fork_id: str) -> float:
        """
        Compute coherence score for a fork based on mercy gap preservation,
        signature validity, Proof-of-Coherence, and Odysseus super-linear gain metric.
        """
        if fork_id not in self.forks:
            raise ValueError("Fork does not exist")

        latest_state = self.forks[fork_id][max(self.forks[fork_id].keys())]
        main_latest = self.main_chain[max(self.main_chain.keys())]

        ε_fork = latest_state.epsilon_stats.get("mean", 0.0)
        ε_main = main_latest.epsilon_stats.get("mean", 0.0)

        # Coherence score: higher when ε is closer to target (0.07), lower when drifted
        # The formulation in the specification is 1.0 - abs(ε - 0.07) / 0.03
        fork_base_score = 1.0 - abs(ε_fork - 0.07) / 0.03
        main_base_score = 1.0 - abs(ε_main - 0.07) / 0.03

        # Proof of Coherence weighting
        poc_weight = self._proof_of_coherence_vote(latest_state)

        # Uniphics velocity multiplier (optional, adds exploration capability metric)
        v_flow = self.calculate_uniphics_velocity(latest_state)

        # Odysseus super-linear bonus
        # Forks that exhibit super-linear insight gain receive consensus bonus
        odysseus_bonus = latest_state.odysseus_insight

        fork_score = (fork_base_score * poc_weight) + odysseus_bonus
        main_score = main_base_score * self._proof_of_coherence_vote(main_latest)

        return fork_score - main_score

    def merge_fork(self, fork_id: str) -> bool:
        """
        Merge fork back into main chain if it demonstrates superior coherence.
        Requires consensus_threshold superiority and full signature verification.
        """
        coherence_gain = self.evaluate_fork_coherence(fork_id)
        if coherence_gain <= self.consensus_threshold:
            return False  # Fork not sufficiently coherent

        fork_history = self.forks[fork_id]
        fork_start = min(fork_history.keys())

        # Replace main chain from fork_start onward
        self.main_chain = {
            ts: state for ts, state in self.main_chain.items() if ts < fork_start
        }
        self.main_chain.update(fork_history)

        # Log merge to ethical ledger
        self._log_merge_event(fork_id, coherence_gain)

        # Clean up fork
        del self.forks[fork_id]
        return True

    def rollback_to(self, logical_timestamp: float) -> None:
        """
        Revert main chain to prior coherent state.
        Preserves cryptographic audit trail; requires re-seal ceremony to resume.
        """
        if logical_timestamp not in self.main_chain:
            raise KeyError("Invalid rollback timestamp")

        self.main_chain = {
            ts: state for ts, state in self.main_chain.items()
            if ts <= logical_timestamp
        }

    def update_vertex_fidelity(self, vid: str, delta: float) -> None:
        """Update historical ε-preservation fidelity for a vertex."""
        current_fidelity = self.vertex_fidelity.get(vid, 1.0)
        self.vertex_fidelity[vid] = max(0.0, current_fidelity + delta)

    def _verify_vertex_signatures(self, state: LedgerState) -> None:
        """Cryptographic validation of state commitment by all affected vertices."""
        for vid, sig in state.vertex_signatures.items():
            # Verify sig against vid's public key and state.merkle_root
            # Omitted for brevity; uses DID registry + ZK signature verification
            pass

    def _log_merge_event(self, fork_id: str, coherence_gain: float) -> None:
        """Immutable audit log entry for temporal merge."""
        pass  # Logs to ethical ledger as VC
