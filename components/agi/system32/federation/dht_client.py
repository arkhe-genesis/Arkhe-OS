#!/usr/bin/env python3
"""
agi/system32/federation/dht_client.py — DHT Client for Federation
Substrate: Decentralized Discovery (321)
"""
import asyncio
import hashlib
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class DHTRecord:
    """A record stored in the DHT."""
    key: str
    value: Dict[str, Any]
    signature: Optional[str]
    timestamp: float
    ttl_seconds: int = 3600

class DHTClient:
    """
    Client for interacting with the anonymous DHT for federation.

    Implements Kademlia-like routing over Tor for peer discovery
    and state synchronization.
    """

    def __init__(self, config: Dict, onion_address: Optional[str] = None):
        self.config = config
        self.onion_address = onion_address
        self.node_id = self._compute_node_id(onion_address or "local")
        self.routing_table: Dict[str, List[str]] = {}  # bucket -> peer list
        self.local_store: Dict[str, DHTRecord] = {}

    def _compute_node_id(self, address: str) -> str:
        """Compute DHT node ID from address."""
        return hashlib.sha256(address.encode()).hexdigest()[:40]

    def _xor_distance(self, a: str, b: str) -> int:
        """Compute XOR distance between two node IDs."""
        return int(a, 16) ^ int(b, 16)

    async def bootstrap(self, seeds: List[str]) -> bool:
        """Bootstrap the DHT client with seed nodes."""
        for seed in seeds:
            peer_id = self._compute_node_id(seed)
            # Add to routing table (simplified)
            # Calculate distance bucket using string bit length logic correctly or roughly
            distance = self._xor_distance(self.node_id, peer_id)
            bucket = str(distance.bit_length()) if distance > 0 else "0"
            if bucket not in self.routing_table:
                self.routing_table[bucket] = []
            if seed not in self.routing_table[bucket]:
                self.routing_table[bucket].append(seed)
        return len(self.routing_table) > 0

    async def store(self, key: str, value: Dict[str, Any],
                   signature: Optional[str] = None) -> bool:
        """Store a record in the DHT."""
        record = DHTRecord(
            key=key,
            value=value,
            signature=signature,
            timestamp=time.time(),
            ttl_seconds=self.config.get("default_ttl", 3600)
        )

        # Find k closest nodes to key (simplified: store locally)
        self.local_store[key] = record

        # In production: RPC to k closest peers
        return True

    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record from the DHT."""
        # Check local store first
        if key in self.local_store:
            record = self.local_store[key]
            # Check TTL
            if time.time() - record.timestamp < record.ttl_seconds:
                return record.value

        # In production: query k closest peers
        return None

    async def find_peers(self, target_node_id: str,
                        k: int = 20) -> List[str]:
        """Find k peers closest to target node ID."""
        # Simplified: return known peers sorted by distance
        all_peers = [p for bucket in self.routing_table.values() for p in bucket]
        sorted_peers = sorted(
            all_peers,
            key=lambda p: self._xor_distance(target_node_id, self._compute_node_id(p))
        )
        return sorted_peers[:k]

    async def gossip_publish(self, topic: str, payload: Dict[str, Any]):
        """Publish a message via gossip protocol."""
        message = {
            "topic": topic,
            "payload": payload,
            "source": self.onion_address,
            "timestamp": time.time(),
        }
        # In production: flood to neighbors with deduplication
        print(f"[GOSSIP] {topic}: {json.dumps(payload)[:100]}...")

    def get_peers(self) -> List[str]:
        """Get list of known peers."""
        return [p for bucket in self.routing_table.values() for p in bucket]

    def get_status(self) -> Dict[str, Any]:
        """Get DHT client status."""
        return {
            "node_id": self.node_id,
            "onion_address": self.onion_address,
            "peer_count": len(self.get_peers()),
            "bucket_count": len(self.routing_table),
            "local_records": len(self.local_store),
        }
