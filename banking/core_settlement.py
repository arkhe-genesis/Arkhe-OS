#!/usr/bin/env python3
"""
Substrato 200: Core Settlement
Liquidação interbancária com consenso MAC + PQC e validação de Φ_C.
"""

import hashlib
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
import asyncio

@dataclass
class SettlementResult:
    tx_id: str
    amount: float
    status: str
    phi_c_at_execution: float
    temporal_seal: Optional[str] = None
    pqc_signature: Optional[str] = None
    mac_agents_approved: int = 0
    error_reason: Optional[str] = None

class CoreSettlement:
    def __init__(self, phi_bus=None, temporal_chain=None, hsm_signer=None):
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.hsm = hsm_signer
        self.settlement_history: List[SettlementResult] = []
        self._mock_pqc_signer = lambda data: "pqc_sig_" + hashlib.sha256(data).hexdigest()[:16]

    async def get_current_phi_c(self) -> float:
        if self.phi_bus:
            return await self.phi_bus.get_global_coherence()
        return 0.9995  # Default mock healthy value

    async def _mock_mac_consensus(self, agents: List[str], tx_data: Dict) -> int:
        """Simulate MAC consensus. Returns number of approving agents."""
        # Simple mock: if amount > 10M, maybe fewer agents approve if risky, but let's just say all approve.
        return len(agents)

    async def process_settlement(self, sender: str, receiver: str, amount: float, agents: List[str], current_phi_c: Optional[float] = None) -> SettlementResult:
        if current_phi_c is None:
            current_phi_c = await self.get_current_phi_c()

        tx_id = hashlib.sha3_256(f"{sender}-{receiver}-{amount}-{time.time()}".encode()).hexdigest()[:16]

        # 1. Φ_C threshold check
        if current_phi_c < 0.999:
            result = SettlementResult(
                tx_id=tx_id, amount=amount, status="REJECTED",
                phi_c_at_execution=current_phi_c, error_reason="Φ_C below 0.999 threshold"
            )
            self.settlement_history.append(result)
            return result

        # 2. MAC Consensus
        approving_agents = await self._mock_mac_consensus(agents, {"tx_id": tx_id, "amount": amount})
        if approving_agents < 3:
            result = SettlementResult(
                tx_id=tx_id, amount=amount, status="REJECTED",
                phi_c_at_execution=current_phi_c, error_reason="MAC consensus failed (<3 agents)",
                mac_agents_approved=approving_agents
            )
            self.settlement_history.append(result)
            return result

        # 3. PQC Signature via HSM
        tx_data = json.dumps({"tx_id": tx_id, "sender": sender, "receiver": receiver, "amount": amount}, sort_keys=True).encode()
        if self.hsm:
            pqc_sig = await self.hsm.sign(tx_data)
        else:
            pqc_sig = self._mock_pqc_signer(tx_data)

        # 4. Temporal Anchor
        temporal_seal = None
        if self.temporal:
            temporal_seal = await self.temporal.anchor_event("core_settlement", {"tx_id": tx_id, "amount": amount})
        else:
            temporal_seal = hashlib.sha256(tx_data + str(time.time()).encode()).hexdigest()[:24]

        result = SettlementResult(
            tx_id=tx_id, amount=amount, status="SETTLED",
            phi_c_at_execution=current_phi_c, temporal_seal=temporal_seal,
            pqc_signature=pqc_sig, mac_agents_approved=approving_agents
        )
        self.settlement_history.append(result)
        return result
