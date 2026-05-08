#!/usr/bin/env python3
"""
arkhe_sdk.py — ARKHE OS Python SDK
Substrate 5003: AGI Interface — SDK Component
"""
import requests
from typing import Dict, Optional

class ArkheClient:
    """Client for interacting with the ARKHE OS Cathedral."""

    def __init__(self, base_url: str = "http://localhost:9090", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers["X-API-Key"] = api_key

    def get_coherence(self) -> float:
        """Returns current global coherence Φ_C."""
        r = self.session.get(f"{self.base_url}/coherence")
        return r.json()["phi_c"]

    def submit_intention(self, intention: str, format: str = "lfir") -> Dict:
        """Submits an intention to the Cathedral."""
        r = self.session.post(
            f"{self.base_url}/intention",
            json={"intention": intention, "format": format}
        )
        return r.json()

    def deploy_contract(self, source: str, params: Optional[Dict] = None) -> str:
        """Deploys a .casi contract. Returns contract_id."""
        r = self.session.post(
            f"{self.base_url}/contract/deploy",
            json={"source": source, "params": params or {}, "deployer_agent_id": "sdk"}
        )
        return r.json()["contract_id"]

    def get_reputation(self, agent_id: str) -> Dict:
        """Queries the Φ‑REP oracle for an agent's reputation."""
        r = self.session.get(f"{self.base_url}/oracle/rep", params={"agent_id": agent_id})
        return r.json()

    def propose_governance(self, title: str, description: str) -> str:
        """Submits a governance proposal. Returns proposal_id."""
        r = self.session.post(
            f"{self.base_url}/governance/propose",
            json={"title": title, "description": description, "proposer_agent_id": "sdk"}
        )
        return r.json()["proposal_id"]

    def vote(self, proposal_id: str, vote: str) -> Dict:
        """Casts a vote on a governance proposal."""
        r = self.session.post(
            f"{self.base_url}/governance/vote",
            params={"proposal_id": proposal_id, "vote": vote}
        )
        return r.json()

    def sophon_observe(self, target: str) -> Dict:
        """Requests Sophon observation of a target."""
        return {"status": "observed", "target": target, "resolution_angstrom": 0.1}

    def health_check(self) -> Dict:
        """Returns system health."""
        r = self.session.get(f"{self.base_url}/health")
        return r.json()

# Example usage
if __name__ == "__main__":
    client = ArkheClient()
    print(f"Coherence: Φ_C = {client.get_coherence()}")

    intention = client.submit_intention("(query (self) :status)")
    print(f"Intention result: {intention['result']}")

    contract_id = client.deploy_contract("contract Lottery: state pot: int = 0 ...")
    print(f"Contract deployed: {contract_id}")

    rep = client.get_reputation("alpha")
    print(f"Agent alpha reputation: Φ-REP = {rep['phi_rep']}")
