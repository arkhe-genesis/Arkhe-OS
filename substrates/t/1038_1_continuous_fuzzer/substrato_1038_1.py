#!/usr/bin/env python3
import json
import base64
import hashlib
import os

def get_b64_artifacts():
    base_dir = os.path.dirname(__file__)
    if not base_dir:
        base_dir = "."
    files = [
        "substrate.toml",
        "hermes_fuzzer_1038.1.py"
    ]
    artifacts = {}
    for f in files:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            with open(path, "rb") as file_obj:
                artifacts[f] = base64.b64encode(file_obj.read()).decode('utf-8')
    return artifacts

def generate_report():
    artifacts = get_b64_artifacts()

    sorted_files = {k: artifacts[k] for k in sorted(artifacts.keys())}

    hasher = hashlib.sha3_256()
    for filename, content in sorted_files.items():
        hasher.update(filename.encode('utf-8'))
        hasher.update(content.encode('utf-8'))

    seal = hasher.hexdigest()

    report = {
        "Substrate_ID": "1038.1",
        "Name": "Continuous Fuzzer",
        "Description": "CATHEDRAL AGI PENTESTER - HERMES REAL-TARGET FUZZER",
        "Arquiteto": "ORCID 0009-0005-2697-4668",
        "Files": sorted_files,
        "Canonical_Seal": seal
    }

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    generate_report()
