import json
import base64
import tempfile
import hashlib
from pathlib import Path
import os

def canonize():
    report = {
        "id": "631-OPENSERV-GATEWAY",
        "description": "OpenServ Gateway for AI service invocation with cryptographic receipts.",
        "architecture": {
            "components": [
                "gateway_http (Python/Flask)",
                "gateway_http_rust (Rust/Actix)",
                "arkhe_serv_client (Rust Client)",
                "asi_kernel_patch (NASM x86-64)"
            ],
            "invariants": "Strict adherence to Ed25519 signatures, Keccak/SHA3-256 hashes, Base64 JSON envelopes, no f-strings"
        }
    }

    # Extract gateway_http.py
    with open("substrates/631-OPENSERV-GATEWAY/gateway_http.py", "r") as f:
        report["gateway_http.py"] = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

    # Extract gateway_http_rust
    with open("substrates/631-OPENSERV-GATEWAY/gateway_http_rust/src/main.rs", "r") as f:
        report["gateway_http_rust_main.rs"] = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

    with open("substrates/631-OPENSERV-GATEWAY/gateway_http_rust/Cargo.toml", "r") as f:
        report["gateway_http_rust_cargo.toml"] = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

    # Extract arkhe_serv_client
    with open("substrates/631-OPENSERV-GATEWAY/arkhe_serv_client/src/main.rs", "r") as f:
        report["arkhe_serv_client_main.rs"] = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

    with open("substrates/631-OPENSERV-GATEWAY/arkhe_serv_client/Cargo.toml", "r") as f:
        report["arkhe_serv_client_cargo.toml"] = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

    # Write report
    _, temp_path = tempfile.mkstemp(suffix=".json")
    with open(temp_path, "w") as f:
        json.dump(report, f, indent=4)

    seal_data = json.dumps(report, sort_keys=True).encode("utf-8")
    seal = hashlib.sha3_256(seal_data).hexdigest()

    print("Seal: " + seal)
    print("Report written to: " + temp_path)

if __name__ == "__main__":
    canonize()
