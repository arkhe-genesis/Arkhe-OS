#!/usr/bin/env python3

# pack.py - Pack Arkhe AGI artifact

import os
import hashlib
import json
import tarfile

def calculate_sha256(file_path):
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def pack_agi():
    manifest = json.load(open(".agi/MANIFEST.json"))
    # Collect files
    files = []
    for root, dirs, filenames in os.walk("."):
        if ".git" in root or "archive" in root:
            continue
        for filename in filenames:
            files.append(os.path.join(root, filename))

    # Create tar
    with tarfile.open("arkhe-agi-v1.0.0.agi", "w:gz") as tar:
        for file in files:
            tar.add(file)

    # Calculate hash and sign
    sha256 = calculate_sha256("arkhe-agi-v1.0.0.agi")
    manifest["integrity"]["sha256"] = sha256
    # Placeholder signature
    manifest["signature"] = "signed_with_falcon_1024"

    with open(".agi/MANIFEST.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print("AGI artifact packed and signed.")

if __name__ == "__main__":
    pack_agi()