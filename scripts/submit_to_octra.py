#!/usr/bin/env python3
"""
submit_to_octra.py
Submits verifiable generated proofs (root hashes) to the OCTRA API.
"""
import requests
import json
import argparse
import time

def submit_root_hash(root_hash, dataset_info, backend_info):
    """
    Submits a given proof root hash to OCTRA.
    """
    print(f"🚀 Submitting to OCTRA API...")
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root_hash": root_hash,
        "dataset": dataset_info,
        "backend": backend_info,
        "protocol_version": "v∞.327.3"
    }

    print(json.dumps(payload, indent=2))

    # Mocking actual API submission:
    # response = requests.post("https://api.octra.network/submit", json=payload)
    # response.raise_for_status()

    print("✅ Successfully submitted to OCTRA (Mocked).")
    return payload

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit to OCTRA")
    parser.add_argument("--root-hash", required=True, help="Merkle root hash of proofs")
    args = parser.parse_args()

    dataset_info = {
        "name": "Crystal Brain v∞.15",
        "fingerprint": 0.58
    }

    backend_info = {
        "type": "ZEE200",
        "security_bits": 80,
        "post_quantum": True
    }

    submit_root_hash(args.root_hash, dataset_info, backend_info)
