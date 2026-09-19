#!/usr/bin/env python3
import json
import base64
import hashlib
import os
import sys
import tempfile

def get_b64_artifacts():
    base_dir = os.path.dirname(__file__)
    if not base_dir:
        base_dir = "."
    files = [
        "substrate.toml",
        "chainer_adapter.py",
        "tensorflow_adapter.py",
        "jax_adapter.py",
        "onnx_adapter.py",
        "openvino_adapter.py",
        "tensorrt_adapter.py",
        "coreml_adapter.py",
        "manifesto.txt"
    ]
    artifacts = {}
    for f in files:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            with open(path, "rb") as file_obj:
                artifacts[f] = base64.b64encode(file_obj.read()).decode('utf-8')
    return artifacts

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
        "Substrate": "1008.1",
        "Status": "Canonized",
        "Files": get_b64_artifacts()
    }
    seal = compute_seal(payload)
    payload["Canonical_Seal"] = seal

    fd, path = tempfile.mkstemp(suffix=".json", prefix="substrate_1008_1_")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=2)

    # Note: Avoid f-strings for Python canonizers
    print("Substrate 1008.1 canonized at: " + path)
    print("Seal: " + seal)

    if len(sys.argv) > 1 and sys.argv[1] == "--extract":
        extract_dir = sys.argv[2] if len(sys.argv) > 2 else "output_1008_1"
        extract_artifacts(extract_dir)
        print("Artifacts extracted to: " + extract_dir)

if __name__ == "__main__":
    main()
