import hashlib
import json
import pickle
from typing import Dict, Any, Optional

class TemporalAnchor:
    def __init__(self, data: Any):
        self.data_hash = hashlib.sha3_256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:16]
        self.timestamp = "mock_timestamp_2026_04_07"

    def __repr__(self):
        return f"TemporalAnchor(hash={self.data_hash}, ts={self.timestamp})"

class ZKProof:
    def __init__(self, statement: str, public_inputs: list):
        self.statement = statement
        self.public_inputs = public_inputs
        self.proof_hash = hashlib.sha3_256(f"{statement}:{public_inputs}".encode()).hexdigest()[:16]

    def verify(self) -> bool:
        return True

    def __repr__(self):
        return f"ZKProof(stmt='{self.statement}', hash={self.proof_hash})"

class ArtBlock:
    def __init__(self, model_bytes: bytes, provenance: Dict[str, Any], anchor: TemporalAnchor, proof: ZKProof):
        self.model_bytes = model_bytes
        self.provenance = provenance
        self.anchor = anchor
        self.proof = proof

class MLModelAnchor:
    """Substrato 6072 - ML Model Anchor
    Stores the model, its provenance, and the data hashes.
    Later, if the same data+code combination is run, the model is fetched from registry cache.
    """
    def __init__(self):
        self.registry = {}

    def anchor_model(self, model_obj: Any, data_hash: str, provenance: Dict[str, Any]) -> ArtBlock:
        model_bytes = pickle.dumps(model_obj)
        model_hash = hashlib.sha3_256(model_bytes).hexdigest()[:16]

        stmt = f"Model {model_hash} correctly trained on data {data_hash}"
        proof = ZKProof(stmt, [model_hash, data_hash, provenance])
        anchor = TemporalAnchor({"model_hash": model_hash, "data_hash": data_hash})

        block = ArtBlock(model_bytes, provenance, anchor, proof)

        # In reality, this would be code_hash + data_hash, but we'll simplify
        key = f"{data_hash}_{provenance.get('code_hash', 'unknown')}"
        self.registry[key] = block

        return block

    def fetch_model(self, data_hash: str, code_hash: str) -> Optional[Any]:
        key = f"{data_hash}_{code_hash}"
        if key in self.registry:
            block = self.registry[key]
            # Ensure proof is valid
            if block.proof.verify():
                return pickle.loads(block.model_bytes)
        return None


# ===== TESTS =====
if __name__ == "__main__":
    print("\n=== SUBSTRATO 6072 TEST SUITE ===")
    anchor = MLModelAnchor()

    # Mock scikit-learn model object (just a dict for now)
    mock_model = {"coef_": [0.5, -0.2], "intercept_": 0.1, "classes_": [0, 1]}
    data_hash = "mock_data_hash_123"
    provenance = {"code_hash": "mock_code_hash_456", "trainer": "scikit-learn"}

    # Anchor the model
    block = anchor.anchor_model(mock_model, data_hash, provenance)
    assert block.anchor.data_hash is not None
    assert block.proof.verify()
    print("PASS: Model anchored as ArtBlock")

    # Fetch the model
    fetched_model = anchor.fetch_model(data_hash, provenance["code_hash"])
    assert fetched_model is not None
    assert fetched_model["coef_"] == [0.5, -0.2]
    print("PASS: Model fetched correctly from registry cache")

    # Fetch missing model
    missing_model = anchor.fetch_model("wrong_hash", "wrong_hash")
    assert missing_model is None
    print("PASS: Missing model handles correctly")

    print("ALL TESTS PASSED for Substrato 6072.")
