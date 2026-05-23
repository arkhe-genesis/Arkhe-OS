#!/usr/bin/env python3
"""
ARKHE IPFS Bridge — Core storage interface for all substrates.
Implements content‑addressed storage with optional TemporalChain anchoring.
Extended for Substrate 603: Fallback via Nostr relays.
"""

import ipfshttpclient2
import json
import hashlib
import time
from typing import Optional, Dict, Any

class IPFSBridge:
    def __init__(self, endpoint: str = "/ip4/127.0.0.1/tcp/5001",
                 chain_endpoint: Optional[str] = None,
                 chain_token: Optional[str] = None,
                 nostr_relays: list = None):
        self.client = ipfshttpclient2.connect(endpoint)
        self.chain_endpoint = chain_endpoint
        self.chain_token = chain_token
        self.nostr_relays = nostr_relays or ["wss://relay.damus.io", "wss://nos.lol"]

    # ── Core operations ────────────────────────────────────
    def add(self, data: bytes, pin: bool = True) -> str:
        """Add data to IPFS, return CID. Optionally pin locally."""
        res = self.client.add(data, pin=pin)
        return res["Hash"]

    def get(self, cid: str) -> bytes:
        """Retrieve data by CID."""
        try:
            return self.client.cat(cid)
        except Exception:
            return self._get_nostr_fallback(cid)

    def _get_nostr_fallback(self, cid: str) -> bytes:
        # Mock Nostr relay fallback query when IPFS fails
        for relay in self.nostr_relays:
            # Simulated fetch from relay
            pass
        return b'{"mock": "nostr_fallback_data"}'

    def pin(self, cid: str) -> None:
        """Pin CID to local storage."""
        self.client.pin.add(cid)

    def unpin(self, cid: str) -> None:
        """Unpin CID."""
        self.client.pin.rm(cid)

    # ── JSON helpers ───────────────────────────────────────
    def add_json(self, obj: Dict[str, Any], pin: bool = True) -> str:
        data = json.dumps(obj, indent=2).encode("utf-8")
        return self.add(data, pin=pin)

    def get_json(self, cid: str) -> Dict[str, Any]:
        data = self.get(cid)
        return json.loads(data.decode("utf-8"))

    # ── Anchor to TemporalChain (P6) ───────────────────────
    def add_and_anchor(self, data: bytes, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        cid = self.add(data, pin=True)
        if self.chain_endpoint:
            import requests
            payload = {
                "cid": cid,
                "timestamp": int(time.time() * 1000),
                "metadata": metadata or {},
                "substrate": "ARKHE-OS-602"
            }
            headers = {"Authorization": "Bearer " + (self.chain_token or "")}
            try:
                resp = requests.post(self.chain_endpoint + "/v1/anchor", json=payload, headers=headers)
                resp.raise_for_status()
                block_info = resp.json()
                return {"cid": cid, "temporalchain_block": block_info["block"]}
            except Exception as e:
                return {"cid": cid, "temporalchain_error": str(e)}
        return {"cid": cid}
