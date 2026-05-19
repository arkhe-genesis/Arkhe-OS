import json
from typing import Dict
from pathlib import Path

def anchor_cor_proof_token(token: Dict, out_path: str = "cor_proof_temporal.jsonl"):
    """
    Appends a Token Arkhe (generated from a COR Proof) into a TemporalChain
    anchor file using an append-only JSONL format to prevent memory blowups.
    """
    out_file = Path(out_path)

    # Use deterministic serialization
    line = json.dumps(token, sort_keys=True)

    with open(out_file, "a") as f:
        f.write(line + "\n")

    return True
