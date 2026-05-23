#!/usr/bin/env python3
"""
ARKHE IPFS Bridge — Core storage interface for all substrates.
Implements content‑addressed storage with optional TemporalChain anchoring.
Extended with Nostr relay fallback (Substrate 603).
"""

import ipfshttpclient2
import json
import hashlib
import time
import requests
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
        """Retrieve data by CID, with fallback to Nostr/Hashtree if not found."""
        try:
            return self.client.cat(cid)
        except Exception as e:
            # Fallback to Nostr relays (Hashtree protocol)
            print("IPFS fetch failed, falling back to Nostr relays for CID: " + cid)
            return self._fetch_from_nostr(cid)

    def _fetch_from_nostr(self, cid: str) -> bytes:
        """Fallback resolution via Nostr/Hashtree."""
        # This is a model implementation representing the WebRTC/Blossom fallback
        try:
            # Try Blossom server fallback as modeled in Hashtree
            blossom_url = "https://cdn.hashtree.cc/" + cid
            resp = requests.get(blossom_url, timeout=10)
            if resp.status_code == 200:
                return resp.content
        except Exception:
            pass
        raise Exception("Failed to resolve CID from IPFS and Nostr fallback: " + cid)

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
            payload = {
                "cid": cid,
                "timestamp": int(time.time() * 1000),
                "metadata": metadata or {},
                "substrate": "ARKHE-OS-602"
            }
            headers = {"Authorization": "Bearer " + str(self.chain_token)}
            try:
                resp = requests.post(self.chain_endpoint + "/v1/anchor", json=payload, headers=headers)
                resp.raise_for_status()
                block_info = resp.json()
                return {"cid": cid, "temporalchain_block": block_info["block"]}
            except Exception as e:
                return {"cid": cid, "temporalchain_error": str(e)}
        return {"cid": cid}
