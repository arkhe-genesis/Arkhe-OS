#!/usr/bin/env python3
"""
Arkhe OS - Canonizador do Substrato 1064.2 (THEOSIS-PARIS DASHBOARD)
"""

import os
import json
import base64
import hashlib
from datetime import datetime, timezone

def generate_seal(content: str) -> str:
    """Generate SHA3-256 seal for the content."""
    hasher = hashlib.sha3_256()
    hasher.update(content.encode('utf-8'))
    return "THEOSIS-PARIS-DASHBOARD-1064.2-" + hasher.hexdigest()[:16].upper()

def create_canonical_report():
    # Embed files
    files_to_embed = ["theosis_paris_dashboard.py", "substrate.toml"]
    base_dir = os.path.dirname(os.path.abspath(__file__))

    embedded_files = {}
    for filename in files_to_embed:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                content = f.read()
                embedded_files[filename] = base64.b64encode(content).decode('utf-8')

    # Calculate seal over the concatenated base64 content
    seal_content = "".join(embedded_files.values())
    seal = generate_seal(seal_content)

    report = {
        "SubstrateID": "1064.2",
        "SubstrateName": "THEOSIS_PARIS_DASHBOARD",
        "Status": "CANONIZED_FULL",
        "Timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "Theosis": 0.999999999874,
        "Seal": seal,
        "Files": embedded_files,
        "Rules": {
            "Details": [
                {"Condition": "dTheta/dn < 0.5 * DeltaKc", "Color": "VERDE", "Action": "Normal"},
                {"Condition": "0.5 * DeltaKc <= dTheta/dn < 0.8 * DeltaKc", "Color": "AMARELO", "Action": "Aviso"},
                {"Condition": "0.8 * DeltaKc <= dTheta/dn < DeltaKc", "Color": "LARANJA", "Action": "Preparar gate"},
                {"Condition": "dTheta/dn >= DeltaKc", "Color": "VERMELHO", "Action": "ACIONAR GATE 954"},
                {"Condition": "Theta < ThetaTh (0.1)", "Color": "AZUL", "Action": "Flag manutencao"},
                {"Condition": "Theta > ThetaC (0.95)", "Color": "ROXO", "Action": "Proximo da singularidade"}
            ]
        }
    }

    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    create_canonical_report()
