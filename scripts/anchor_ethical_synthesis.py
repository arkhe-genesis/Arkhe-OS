import sys
import os
import json
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from physics.ethical_synthesis import MerkabahEthicalEngine
except ImportError:
    # Handle if path is different in sandbox
    sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
    from physics.ethical_synthesis import MerkabahEthicalEngine

def anchor_synthesis():
    engine = MerkabahEthicalEngine()

    dilemmas = [
        "Dilema: Mentir para salvar uma vida?",
        "Dilema do Prisioneiro: Lealdade familiar vs. Liberdade individual"
    ]

    anchored_assets = []

    print("=== ARKHE ETHICAL SYNTHESIS ANCHORING ===")

    for dilemma in dilemmas:
        result = engine.ethical_synthesis(dilemma)

        # Simulate anchoring to KnowledgeAsset.sol
        token_id = len(anchored_assets) + 1
        anchor_data = {
            "token_id": token_id,
            "dilemma": dilemma,
            "action": result.action,
            "fidelity": result.fidelity,
            "metadata_uri": f"qhttp://arkhe-block/synthesis/{result.metadata}",
            "anchored_at": datetime.now().isoformat(),
            "status": "ANCHORED"
        }

        anchored_assets.append(anchor_data)
        print(f"✅ Anchored AKA #{token_id}: {result.action[:50]}...")

    print("\n--- PRIMORDIAL CREATION ---")
    domains = ["Biofísica", "Matemática Pura", "Música"]
    for domain in domains:
        asset = engine.primordial_creation(domain)
        asset.id = len(anchored_assets) + 4 # Start from #7 as per user prompt

        anchor_data = {
            "token_id": asset.id,
            "domain": asset.domain,
            "synthesis_type": asset.synthesis_type,
            "description": asset.description,
            "impact": asset.impact,
            "fidelity": asset.fidelity,
            "metadata_uri": f"qhttp://arkhe-block/primordial/{asset.id}",
            "anchored_at": datetime.now().isoformat(),
            "status": "ANCHORED_PRIMORDIAL"
        }
        anchored_assets.append(anchor_data)
        print(f"✨ Anchored Primordial AKA #{asset.id}: {asset.synthesis_type}")

    # Write results to a report file
    report_path = "arkhe_ethical_anchoring_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(anchored_assets, f, indent=2)

    print(f"\nReport generated: {report_path}")
    print("🜏 ARKHE-NC CONVERGENCE FINALIZED.")

if __name__ == "__main__":
    anchor_synthesis()
