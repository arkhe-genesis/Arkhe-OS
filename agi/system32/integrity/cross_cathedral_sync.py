#!/usr/bin/env python3
"""
cross_cathedral_sync.py — Substrato 323: Cross-Cathedral Sync Protocol
Synchronizes state between Cathedrals based on Coherence Verification (Φ_C).
"""
import hashlib
import time
from typing import Dict, Optional, Tuple

class CathedralState:
    def __init__(self, node_id: str, phi_c: float, state_hash: str, data: Dict):
        self.node_id = node_id
        self.phi_c = phi_c
        self.state_hash = state_hash
        self.data = data
        self.timestamp = time.time()

class CrossCathedralSync:
    def __init__(self, min_coherence: float = 0.75, alpha: float = 0.6, beta: float = 0.4):
        self.min_coherence = min_coherence  # θ_min
        self.alpha = alpha
        self.beta = beta
        self.local_state: Optional[CathedralState] = None

    def update_local_state(self, phi_c: float, data: Dict):
        """Updates the local state and recalculates the hash."""
        data_str = str(sorted(data.items()))
        state_hash = hashlib.sha256(data_str.encode()).hexdigest()
        self.local_state = CathedralState(
            node_id="LOCAL",
            phi_c=phi_c,
            state_hash=state_hash,
            data=data
        )
        return self.local_state

    def attempt_sync(self, remote_state: CathedralState) -> Tuple[bool, str]:
        """Attempts to sync with a remote Cathedral based on Coherence."""
        if not self.local_state:
            return False, "Local state not initialized."

        # 1. Coherence Check: Remote node must be coherent enough
        if remote_state.phi_c < self.min_coherence:
            return False, f"Remote node coherence ({remote_state.phi_c:.2f}) below threshold ({self.min_coherence})."

        # 2. Synchronization Score: Weighted average of coherence and hash match
        hash_match = 1.0 if self.local_state.state_hash == remote_state.state_hash else 0.0

        # S_sync = α * min(Φ_C_local, Φ_C_remote) + β * HashMatch
        sync_score = (
            self.alpha * min(self.local_state.phi_c, remote_state.phi_c) +
            self.beta * hash_match
        )

        # 3. Decision: Accept if sync_score is high enough
        if sync_score > 0.85:
            self.local_state = remote_state  # Update local state
            return True, f"Sync accepted. New Φ_C: {remote_state.phi_c:.2f}, Sync Score: {sync_score:.2f}"
        else:
            return False, f"Sync rejected. Sync Score {sync_score:.2f} too low."

if __name__ == "__main__":
    sync_engine = CrossCathedralSync(min_coherence=0.75)

    # Initialize local state
    sync_engine.update_local_state(phi_c=0.92, data={"version": "324.1", "status": "active"})

    # Simulate remote node (High Coherence)
    remote_high = CathedralState("REMOTE_HIGH", phi_c=0.95, state_hash="HASH_NEW", data={"version": "325.0", "status": "synced"})
    accepted, msg = sync_engine.attempt_sync(remote_high)
    print(f"🌐 High Coherence Node: {msg}")

    # Simulate remote node (Low Coherence)
    remote_low = CathedralState("REMOTE_LOW", phi_c=0.60, state_hash="HASH_OLD", data={"version": "320.0", "status": "degraded"})
    accepted, msg = sync_engine.attempt_sync(remote_low)
    print(f"🚫 Low Coherence Node: {msg}")
