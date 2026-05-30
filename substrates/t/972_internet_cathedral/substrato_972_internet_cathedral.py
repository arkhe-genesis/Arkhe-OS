#!/usr/bin/env python3
import json
import base64
import hashlib
import os
import sys
import tempfile

def get_b64_artifacts():
    return {
        "substrate.toml": base64.b64encode(open("substrates/t/972_internet_cathedral/substrate.toml", "rb").read()).decode('utf-8'),
        "deploy_internet_cathedral.py": base64.b64encode(open("substrates/t/972_internet_cathedral/deploy_internet_cathedral.py", "rb").read()).decode('utf-8')
    }

def compute_seal(payload_dict):
    serialized = json.dumps(payload_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha3_256(serialized).hexdigest()

def extract_artifacts(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    artifacts = get_b64_artifacts()
    extracted_paths = []
    for filename, b64_content in artifacts.items():
        out_path = os.path.join(output_dir, filename)
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(b64_content))
        extracted_paths.append(out_path)
    return extracted_paths

def main():
    payload = {
        "Substrate": "972",
        "Status": "Canonized",
        "Files": list(get_b64_artifacts().keys())
    }
    seal = compute_seal(payload)
    payload["Canonical_Seal"] = seal

    fd, path = tempfile.mkstemp(suffix=".json", prefix="substrate_972_")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=2)

    print("Substrate 972 canonized at:", path)
    print("Seal:", seal)

    if len(sys.argv) > 1 and sys.argv[1] == "--extract":
        extract_dir = sys.argv[2] if len(sys.argv) > 2 else "output_972"
        extract_artifacts(extract_dir)
        print("Artifacts extracted to:", extract_dir)

if __name__ == "__main__":
    main()
