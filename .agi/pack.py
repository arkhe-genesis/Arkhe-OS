#!/usr/bin/env python3
"""Pack the Arkhe AGI artifact."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = Path(__file__).resolve().parent / "MANIFEST.json"


def build_artifact(output_path: Path = ROOT / "arkhe-agi-v1.0.0.agi") -> None:
    """Assemble the .agi artifact manifest and placeholder package."""
    manifest = json.loads(MANIFEST_PATH.read_text())
    manifest["signature"] = "pending"
    output_path.write_text(json.dumps(manifest, indent=2))
    print(f"Created AGI artifact placeholder: {output_path}")


if __name__ == "__main__":
    build_artifact()
