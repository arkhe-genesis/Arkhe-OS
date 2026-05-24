import hashlib
import json

def generate_canonical_seal(data: dict) -> str:
    """Generates canonical SHA3-256 seal."""
    return hashlib.sha3_256(
        json.dumps(data, sort_keys=True, default=str).encode()
    ).hexdigest()
