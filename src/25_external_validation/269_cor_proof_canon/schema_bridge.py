import hashlib
import json
import time
from typing import Dict

def cor_proof_to_beaver(cor_proof: Dict) -> Dict:
    """
    Translates a COR Proof object (dict) into the kwargs for BEAVER's
    IntelligenceProposition data structure.

    IntelligenceProposition fields expected:
    - statement: str
    - evidence_hashes: List[str]
    - confidence: float
    - analyst_id: str
    """
    claim = cor_proof.get("claim", "")

    # Generate evidence hashes from the COR proof's evidence
    evidence = cor_proof.get("evidence", [])
    evidence_hashes = []
    for item in evidence:
        item_str = json.dumps(item, sort_keys=True)
        item_hash = hashlib.sha3_256(item_str.encode()).hexdigest()
        evidence_hashes.append(f"cor_proof_evidence:{item_hash[:32]}")

    # Heuristic confidence based on the presence of evidence and reasoning atoms
    reasoning_atoms = cor_proof.get("reasoning_atoms", [])
    base_confidence = 0.5

    if len(evidence) > 0:
        base_confidence += 0.2

    if len(reasoning_atoms) > 0:
        base_confidence += 0.2

    # Ensure it's capped at 1.0
    confidence = min(1.0, base_confidence)

    analyst_id = "cor_proof_bridge_parser"

    return {
        "statement": claim,
        "evidence_hashes": evidence_hashes,
        "confidence": confidence,
        "analyst_id": analyst_id,
        "timestamp": time.time()
    }
