#!/usr/bin/env python3
"""
Canonizador do Substrato 1040 — HERMES-CATHEDRAL BRIDGE
"""

import json
import base64
import hashlib
import time

def compute_seal(payload: dict) -> str:
    """Computa o selo canônico SHA3-256 do payload JSON."""
    serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha3_256(serialized.encode('utf-8')).hexdigest()

def get_base64_content(filepath: str) -> str:
    """Lê um arquivo e retorna seu conteúdo em base64."""
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def main():
    bridge_b64 = get_base64_content("substrates/t/1040_hermes_cathedral_bridge/hermes_cathedral_bridge.py")
    toml_b64 = get_base64_content("substrates/t/1040_hermes_cathedral_bridge/substrate.toml")

    # The canonizer must strictly avoid f-strings.
    # We use string concatenation or % formatting to comply with memory guidelines.

    report = {
        "Substrate_ID": "1040",
        "Name": "HERMES-CATHEDRAL BRIDGE",
        "Architect": "ORCID 0009-0005-2697-4668",
        "Version": "2026.06.02",
        "Timestamp": int(time.time()),
        "Files": {
            "hermes_cathedral_bridge.py": bridge_b64,
            "substrate.toml": toml_b64
        }
    }

    seal = compute_seal(report)
    report["Canonical_Seal"] = seal

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
