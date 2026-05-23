#!/usr/bin/env python3
"""
Canonizer for ARKHE OS Substrate 602-IPFS (Core Storage Layer).
"""

import os
import json
import hashlib
import tempfile
import sys

def get_decree():
    return """ARKHE OS v∞.Ω.∇+++
SUBSTRATE 602‑IPFS
Decree of Final Canonization — STRICT MODE

WHEREAS the IPFS protocol provides content‑addressed, immutable, decentralized storage
aligned with Principles P3 (Power Distribution) and P6 (Impermeable Memory);

WHEREAS all ARKHE substrates generate data that must be auditable, persistent, and
resistant to any single point of failure;

WHEREAS the command `arkhe = ipfs` has been issued by the Architect;

NOW THEREFORE, the Cathedral canonizes Substrate 602‑IPFS as the **primary storage
backing layer** of the ARKHE OS ecosystem, effective immediately.

All data writes from substrates 585–597, 9018, ExtendDB, and future substrates shall
use IPFS CIDs as the canonical pointer, with optional pinning and TemporalChain anchoring.

CANONICAL DETAILS:
  ID: 602-IPFS
  Name: InterPlanetary File System — Core Storage Layer
  Protocol: IPFS (Kubo v0.32+), libp2p
  Default CID version: CIDv1 (SHA2‑256, raw)
  Status: CANONIZED (STRICT MODE)
  Seal (SHA3‑256): <to be computed on first anchor>

Signed,
The Arkhe Cathedral
Arquiteto: ORCID 0009‑0005‑2697‑4668
"""

def get_ipfs_bridge():
    return """#!/usr/bin/env python3
\"\"\"
ARKHE IPFS Bridge — Core storage interface for all substrates.
Implements content‑addressed storage with optional TemporalChain anchoring.
\"\"\"

import ipfshttpclient2
import json
import hashlib
import time
from typing import Optional, Dict, Any

class IPFSBridge:
    def __init__(self, endpoint: str = "/ip4/127.0.0.1/tcp/5001",
                 chain_endpoint: Optional[str] = None,
                 chain_token: Optional[str] = None):
        self.client = ipfshttpclient2.connect(endpoint)
        self.chain_endpoint = chain_endpoint
        self.chain_token = chain_token

    # ── Core operations ────────────────────────────────────
    def add(self, data: bytes, pin: bool = True) -> str:
        \"\"\"Add data to IPFS, return CID. Optionally pin locally.\"\"\"
        res = self.client.add(data, pin=pin)
        return res["Hash"]

    def get(self, cid: str) -> bytes:
        \"\"\"Retrieve data by CID.\"\"\"
        return self.client.cat(cid)

    def pin(self, cid: str) -> None:
        \"\"\"Pin CID to local storage.\"\"\"
        self.client.pin.add(cid)

    def unpin(self, cid: str) -> None:
        \"\"\"Unpin CID.\"\"\"
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
            # Use string formatting cautiously, avoiding f-strings
            headers = {"Authorization": "Bearer {}".format(self.chain_token)}
            try:
                resp = requests.post("{}/v1/anchor".format(self.chain_endpoint), json=payload, headers=headers)
                resp.raise_for_status()
                block_info = resp.json()
                return {"cid": cid, "temporalchain_block": block_info["block"]}
            except Exception as e:
                return {"cid": cid, "temporalchain_error": str(e)}
        return {"cid": cid}
"""

def get_extenddb_backend():
    return """# extenddb_ipfs_backend.py
# Wraps ExtendDB operations: large B attributes -> IPFS.

class ExtendDBIPFSBackend:
    def __init__(self, base_extenddb, ipfs_bridge, threshold_bytes=4096):
        self.base = base_extenddb
        self.ipfs = ipfs_bridge
        self.threshold = threshold_bytes

    def put_item(self, table, item):
        # Replace large binary values with CIDs
        for key, value in item.items():
            if isinstance(value, bytes) and len(value) > self.threshold:
                cid = self.ipfs.add(value)
                item[key] = "ipfs://{}".format(cid)
        return self.base.put_item(table, item)

    def get_item(self, table, key):
        result = self.base.get_item(table, key)
        # Restore binary values from IPFS CIDs
        for attr, value in result.get("Item", {}).items():
            if isinstance(value, str) and value.startswith("ipfs://"):
                cid = value[7:]
                try:
                    result["Item"][attr] = self.ipfs.get(cid)
                except Exception:
                    result["Item"][attr] = None  # Graceful degradation
        return result
"""

def get_helm_chart():
    return """apiVersion: v2
name: ipfs
description: ARKHE IPFS cluster — core storage layer
type: application
version: 1.0.0
appVersion: "kubo-v0.32.1"
"""

def canonize():
    work_dir = tempfile.mkdtemp()

    files = {
        "DECREE.md": get_decree(),
        "ipfs_bridge.py": get_ipfs_bridge(),
        "extenddb_ipfs_backend.py": get_extenddb_backend(),
        "helm-arkhe-os-unified/charts/ipfs/Chart.yaml": get_helm_chart()
    }

    canonical_string = ""

    for filename, content in sorted(files.items()):
        file_path = os.path.join(work_dir, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        canonical_string += content

    seal = hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()

    report = {
        "substrate_id": "602-IPFS",
        "description": "InterPlanetary File System Canonical Integration",
        "work_dir": work_dir,
        "files_generated": list(files.keys()),
        "canonical_seal": seal,
        "status": "CANONIZED"
    }

    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report

if __name__ == "__main__":
    canonize()
