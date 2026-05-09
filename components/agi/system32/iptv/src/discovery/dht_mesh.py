"""
dht_mesh.py — Descoberta de peers e canais via DHT sobre Tor.
Integra com Substrato 330 (Federação).
"""
import asyncio
from typing import List, Dict

class IPTVDiscoveryMesh:
    def __init__(self, dht_client, kym_gate, rep_engine):
        self.dht = dht_client
        self.kym = kym_gate
        self.rep = rep_engine

    async def discover_channels(self, max_results: int = 50) -> List[Dict]:
        """Busca canais na DHT e filtra por KYM/Φ-REP."""
        raw_nodes = await self.dht.lookup("iptv:channels")
        verified = []
        for node in raw_nodes[:100]:
            if self.kym.verify_and_grant_access(node["seal"]):
                phi_rep = self.rep.channel_scores.get(node["id"], 0.5)
                verified.append({
                    "id": node["id"],
                    "title": node["title"],
                    "phi_rep": phi_rep,
                    "viewers": node.get("active_viewers", 0)
                })
        # Ordenar por visibilidade (fórmula canônica)
        verified.sort(key=lambda x: x["phi_rep"], reverse=True)
        return verified[:max_results]
