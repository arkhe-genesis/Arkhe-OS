import time
import hashlib
from typing import Dict, Any

class PartnerDiscoveryAPI:
    """API para auto-descoberta e handshake inicial de parceiros na federação."""

    def __init__(self, temporal_chain=None, min_epsilon: float = 2.0, max_epsilon: float = 5.0):
        self.temporal = temporal_chain
        self.min_epsilon = min_epsilon
        self.max_epsilon = max_epsilon
        self.registered_partners = {}

    async def handshake(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processa o handshake inicial com validação mútua."""
        org_id = payload.get("org_id")
        public_key = payload.get("public_key")
        epsilon = payload.get("epsilon_policy")

        if not org_id or not public_key or epsilon is None:
            return {"status": "rejected", "reason": "missing_required_fields"}

        if not (self.min_epsilon <= epsilon <= self.max_epsilon):
            return {"status": "rejected", "reason": "epsilon_policy_out_of_bounds"}

        partner_id = hashlib.sha3_256(f"{org_id}:{public_key}".encode()).hexdigest()[:16]

        self.registered_partners[org_id] = {
            "partner_id": partner_id,
            "epsilon_policy": epsilon,
            "status": "active",
            "registered_at": time.time()
        }

        # Ancorar handshake na TemporalChain
        temporal_seal = None
        if self.temporal:
             temporal_seal = await self.temporal.anchor_event("partner_handshake", {
                  "org_id": org_id,
                  "partner_id": partner_id,
                  "epsilon_policy": epsilon,
                  "timestamp": time.time()
             })

        return {
            "status": "accepted",
            "partner_id": partner_id,
            "temporal_seal": temporal_seal
        }
