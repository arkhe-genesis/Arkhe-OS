#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Substrato 1042 - RBB-CATHEDRAL-BRIDGE
Canonizer script for Substrate 1042.
"""

import json
import base64
import hashlib
import os

def get_b64_artifacts():
    base_dir = os.path.dirname(__file__)
    if not base_dir:
        base_dir = "."
    files = [
        "README.md",
        "decree_1042.md",
        "docker-compose.yml",
        "manifest.json",
        "requirements.txt",
        "scripts/deploy.sh",
        "adapter/Dockerfile.anchor",
        "adapter/Dockerfile.cli",
        "adapter/cathedral_adapter.py",
        "adapter/temporal_anchor.py",
        "tests/test_rbb_cathedral_bridge.py",
        "contracts/RBB_Cathedral_Bridge.sol",
        "contracts/RBB_Cathedral_Permissionamento.sol",
        "prometheus/Dockerfile.exporter",
        "prometheus/cathedral_alerts.yml",
        "prometheus/prometheus.yml",
        "prometheus/theosis_exporter.py",
        "substrate.toml"
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

    dynamic_seal = "1042-RBB-BRIDGE-" + hasher.hexdigest().upper()

    report = {
        "metadata": {
            "substrate": "1042-RBB-CATHEDRAL-BRIDGE",
            "architect": "ORCID 0009-0005-2697-4668",
            "status": "CANONIZED_PROVISIONAL",
            "seal": dynamic_seal
        },
        "Files": sorted_files
    }
    return report

class Substrate1042Canonizer:
    def canonize(self):
        report = generate_report()
        report_path = os.path.join(os.path.dirname(__file__) or ".", "canonized_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return report_path

if __name__ == "__main__":
    canonizer = Substrate1042Canonizer()
    path = canonizer.canonize()
    print("Report generated at:", path)
