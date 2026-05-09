# tzinor/deploy/hashtree/hashtree_bridge.py
import httpx
import json
from typing import Dict
import time

class HashtreeBridge:
    def __init__(self, peer_url="http://localhost:3000"):
        self.client = httpx.AsyncClient(base_url=peer_url)
    
    async def publish_resonance_state(self, session_id: str, phase: float, omega: float, proof_cid: str):
        """Publica estado de ressonância no peer Hashtree (via API)."""
        payload = {
            "session": session_id,
            "phase": phase,
            "omega": omega,
            "proof": proof_cid,
            "timestamp": time.time()
        }
        response = await self.client.post("/api/publish", json=payload)
        return response.json()
    
    async def fetch_proof(self, cid: str) -> Dict:
        """Obtém prova π² por seu CID."""
        response = await self.client.get(f"/ipfs/{cid}")
        return response.json()
