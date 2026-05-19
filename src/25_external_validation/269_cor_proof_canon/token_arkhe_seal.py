import json
import hashlib
import time
from pathlib import Path

def cor_proof_to_token_arkhe(cor_proof_path: str) -> dict:
    """Converts a COR Proof document into a Token Arkhe."""
    with open(cor_proof_path) as f:
        cor_proof = json.load(f)

    # Extract canonical components
    claim = cor_proof.get("claim", "")
    evidence = cor_proof.get("evidence", [])
    reasoning_atoms = cor_proof.get("reasoning_atoms", [])

    # System timestamp generated once to prevent race condition
    sys_time = time.time()

    # Build canonical payload for the Token Arkhe
    payload = {
        "cor_version": cor_proof.get("cor_version", "1.0.0"),
        "level": cor_proof.get("level", 1),
        "claim": claim,
        "evidence_count": len(evidence),
        "reasoning_steps": len(reasoning_atoms),
        "timestamp": cor_proof.get("timestamp", sys_time),
        "metadata": cor_proof.get("metadata", {})
    }

    # Generate header (SHA3-256 of canonical payload sorted by keys)
    payload_str = json.dumps(payload, sort_keys=True)
    header = hashlib.sha3_256(payload_str.encode()).hexdigest()

    # Generate seal
    seal_str = f"{header}:{claim}:{sys_time}"
    seal = hashlib.sha3_256(seal_str.encode()).hexdigest()

    token = {
        "header": header,
        "identity": f"cor_proof_bridge_{Path(cor_proof_path).stem}",
        "semantics": "proposition",
        "payload": payload,
        "seal": seal,
        "timestamp": sys_time,
        "canon": "∞.Ω.∇+++.269.cor_proof_bridge"
    }
    return token
