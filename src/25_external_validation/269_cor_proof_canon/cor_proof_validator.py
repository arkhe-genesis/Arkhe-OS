from typing import Dict, Tuple

def validate_cor_proof(cor_proof: Dict) -> Tuple[bool, str]:
    """
    Validates the basic structural integrity of a COR Proof dict.
    Returns (is_valid, error_message).
    """
    if "cor_version" not in cor_proof:
        return False, "Missing 'cor_version' field"

    if "claim" not in cor_proof:
        return False, "Missing 'claim' field"

    if "evidence" not in cor_proof or not isinstance(cor_proof["evidence"], list):
        return False, "Missing or invalid 'evidence' array"

    if "reasoning_atoms" not in cor_proof or not isinstance(cor_proof["reasoning_atoms"], list):
        return False, "Missing or invalid 'reasoning_atoms' array"

    return True, "Valid"
