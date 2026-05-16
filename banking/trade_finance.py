#!/usr/bin/env python3
"""
Substrato 200: Trade Finance
Smart contracts para comércio exterior com privacidade diferencial.
"""

import hashlib
import time
import json
import random
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class TradeContract:
    contract_id: str
    importer: str
    exporter: str
    amount: float
    status: str  # DRAFT, CONFIRMED, SHIPPED, DELIVERED, SETTLED
    pqc_signature: Optional[str] = None
    created_at: float = 0.0

class TradeFinance:
    VALID_STATES = ["DRAFT", "CONFIRMED", "SHIPPED", "DELIVERED", "SETTLED"]

    def __init__(self, hsm_signer=None, dp_epsilon: float = 1.0):
        self.hsm = hsm_signer
        self.epsilon = dp_epsilon
        self.contracts: Dict[str, TradeContract] = {}
        self._mock_pqc_signer = lambda data: "pqc_sig_" + hashlib.sha256(data).hexdigest()[:16]

    async def create_contract(self, importer: str, exporter: str, amount: float) -> TradeContract:
        contract_id = hashlib.sha3_256(f"tf-{importer}-{exporter}-{amount}-{time.time()}".encode()).hexdigest()[:16]

        contract_data = json.dumps({"id": contract_id, "amount": amount}, sort_keys=True).encode()
        if self.hsm:
            pqc_sig = await self.hsm.sign(contract_data)
        else:
            pqc_sig = self._mock_pqc_signer(contract_data)

        contract = TradeContract(
            contract_id=contract_id,
            importer=importer,
            exporter=exporter,
            amount=amount,
            status="DRAFT",
            pqc_signature=pqc_sig,
            created_at=time.time()
        )
        self.contracts[contract_id] = contract
        return contract

    def update_contract_status(self, contract_id: str, new_status: str) -> TradeContract:
        if contract_id not in self.contracts:
            raise ValueError("Contract not found")

        if new_status not in self.VALID_STATES:
            raise ValueError(f"Invalid status: {new_status}")

        contract = self.contracts[contract_id]
        current_idx = self.VALID_STATES.index(contract.status)
        new_idx = self.VALID_STATES.index(new_status)

        if new_idx <= current_idx:
            raise ValueError(f"Invalid state transition from {contract.status} to {new_status}")

        contract.status = new_status
        return contract

    def get_portfolio_exposure(self) -> Dict[str, float]:
        """Calculates total exposure with differential privacy noise."""
        total_exposure = sum(c.amount for c in self.contracts.values() if c.status != "SETTLED")

        # Apply differential privacy noise
        # using Laplace mechanism roughly approximated
        # Noise magnitude is inversely proportional to epsilon
        noise_scale = 1000.0 / self.epsilon
        noise = random.normalvariate(0, noise_scale)  # simplified DP noise

        noisy_exposure = max(0.0, total_exposure + noise)
        return {
            "total_active_contracts": len([c for c in self.contracts.values() if c.status != "SETTLED"]),
            "dp_noisy_exposure": noisy_exposure,
            "epsilon": self.epsilon
        }
