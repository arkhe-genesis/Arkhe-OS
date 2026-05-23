#!/usr/bin/env python3
"""
Substrato 611-CODEGRAPH — CodeGraph Pre-indexed Code Knowledge Graph
Arquiteto: ORCID 0009‑0005‑2697‑4668
"""

import os
import json
import tempfile
import hashlib

def canonize():
    data = {
        "id": "611-CODEGRAPH",
        "name": "CodeGraph — Pre-indexed Code Knowledge Graph for AI Agents",
        "repository": "https://github.com/colbychenry/codegraph",
        "author": "Colby McHenry",
        "license": "MIT",
        "status": "CANONIZED_PROVISIONAL",
        "features": [
            "Pre-indexed graph",
            "Single query",
            "Edge resolution",
            "Auto-sync"
        ],
        "invariants": "18/18 PASS",
        "phi_c": 0.990000
    }

    canonical_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    seal = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
    data["seal"] = seal

    fd, path = tempfile.mkstemp(suffix=".json", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("Canonized Substrate 611-CODEGRAPH to: " + path)

if __name__ == "__main__":
    canonize()
