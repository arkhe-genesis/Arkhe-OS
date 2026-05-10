#!/usr/bin/env python3
"""
arkhe_sdk.py — ARKHE OS Python SDK
Substrate 5003: AGI Interface — SDK Component
"""
import requests
import asyncio
import websockets
import json
from typing import Dict, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class IntentionResult:
    intention_id: str
    coherence_score: float
    result: str
    attestation: str
    timestamp: float

class ArkheClient:
    """Client for interacting with the ARKHE OS Cathedral via Nexus API."""

    def __init__(self, base_url: str = "http://localhost:9090", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers["X-API-Key"] = api_key

    def get_coherence(self) -> Dict:
        """Returns current global coherence Φ_C and related metrics."""
        r = self.session.get(f"{self.base_url}/coherence")
        r.raise_for_status()
        return r.json()

    def submit_intention(self, intention: str, format: str = "lfir",
                        coherence_min: float = 0.7, context: Optional[Dict] = None) -> IntentionResult:
        """Submits an intention to the Cathedral."""
        payload = {
            "intention": intention,
            "format": format,
            "coherence_min": coherence_min,
            "context": context or {}
        }
        r = self.session.post(f"{self.base_url}/intention", json=payload)
        r.raise_for_status()
        data = r.json()
        return IntentionResult(**data)

    def deploy_contract(self, source: str, params: Optional[Dict] = None,
                       deployer_id: str = "sdk", coherence_min: float = 0.7) -> Dict:
        """Deploys a .casi contract. Returns contract metadata."""
        payload = {
            "source": source,
            "params": params or {},
            "deployer_agent_id": deployer_id,
            "coherence_min": coherence_min
        }
        r = self.session.post(f"{self.base_url}/contract/deploy", json=payload)
        r.raise_for_status()
        return r.json()

    def get_reputation(self, agent_id: str) -> Dict:
        """Queries the Φ‑REP oracle for an agent's reputation."""
        r = self.session.get(f"{self.base_url}/oracle/rep", params={"agent_id": agent_id})
        r.raise_for_status()
        return r.json()

    def propose_governance(self, title: str, description: str,
                          proposer_id: str = "sdk", threshold: float = 0.75) -> Dict:
        """Submits a governance proposal. Returns proposal metadata."""
        payload = {
            "title": title,
            "description": description,
            "proposer_agent_id": proposer_id,
            "coherence_threshold": threshold
        }
        r = self.session.post(f"{self.base_url}/governance/propose", json=payload)
        r.raise_for_status()
        return r.json()

    def vote(self, proposal_id: str, vote: str) -> Dict:
        """Casts a vote on a governance proposal."""
        r = self.session.post(
            f"{self.base_url}/governance/vote",
            params={"proposal_id": proposal_id, "vote": vote}
        )
        r.raise_for_status()
        return r.json()

    def sophon_observe(self, target: str, resolution: float = 1.0, duration: float = 60.0) -> Dict:
        """Requests Sophon observation of a target."""
        payload = {"target": target, "resolution_angstrom": resolution, "duration_seconds": duration}
        r = self.session.post(f"{self.base_url}/sophon/observe", json=payload)
        r.raise_for_status()
        return r.json()

    def health_check(self) -> Dict:
        """Returns system health."""
        r = self.session.get(f"{self.base_url}/health")
        r.raise_for_status()
        return r.json()

    async def subscribe_events(self, callback):
        """Subscribe to real-time events via WebSocket."""
        ws_url = self.base_url.replace("http", "ws") + "/ws/events"
        async with websockets.connect(ws_url) as websocket:
            while True:
                message = await websocket.recv()
                event = json.loads(message)
                await callback(event)

# Example usage
if __name__ == "__main__":
    client = ArkheClient()

    # Check coherence
    coh = client.get_coherence()
    print(f"Coherence: Φ_C = {coh['phi_c']} ({coh['trend']})")

    # Submit intention
    intention = client.submit_intention("(query (self) :status)")
    print(f"Intention result: {intention.result}")
    print(f"Attestation: {intention.attestation}")

    # Deploy contract
    contract_source = """
    contract Lottery:
      state pot: int = 0
      state ticket_price: int = 1
      func buy_ticket(player: address):
        require(msg.value >= ticket_price)
        pot += msg.value
    """
    contract = client.deploy_contract(contract_source, params={"ticket_price": 1})
    print(f"Contract deployed: {contract['contract_id']}")

    # Query reputation
    rep = client.get_reputation("alpha")
    print(f"Agent alpha reputation: Φ-REP = {rep['phi_rep']}")

    # Governance
    proposal = client.propose_governance(
        title="Enable edge inference",
        description="Allow inference on devices with Φ_C ≥ 0.70"
    )
    print(f"Proposal submitted: #{proposal['proposal_id']}")

    # Sophon observation
    obs = client.sophon_observe("Earth", resolution=0.1, duration=300)
    print(f"Observation initiated: {obs['observation_id']}")
