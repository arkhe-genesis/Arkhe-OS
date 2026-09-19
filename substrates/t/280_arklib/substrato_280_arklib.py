import json
import base64
import hashlib
import os
import sys

def encode_file(filepath):
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def get_b64_artifacts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    artifacts = {}

    # Root level files
    artifacts["substrate.toml"] = encode_file(os.path.join(base_dir, "substrate.toml"))
    artifacts["MANIFESTO.md"] = encode_file(os.path.join(base_dir, "MANIFESTO.md"))
    artifacts["pyproject.toml"] = encode_file(os.path.join(base_dir, "pyproject.toml"))

    # Package files
    arklib_dir = os.path.join(base_dir, "arklib")
    for filename in os.listdir(arklib_dir):
        if filename.endswith(".py"):
            artifacts["arklib/" + filename] = encode_file(os.path.join(arklib_dir, filename))

    return artifacts

def compute_seal(payload_dict):
    serialized = json.dumps(payload_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha3_256(serialized).hexdigest()

def main():
    artifacts = get_b64_artifacts()
    payload = {
        "Substrate": "280",
        "Status": "Canonized",
        "Files": artifacts
    }

    seal = compute_seal(payload)
    payload["Canonical_Seal"] = "sha3-256:" + seal

    print(json.dumps(payload, indent=4))

if __name__ == "__main__":
    main()
