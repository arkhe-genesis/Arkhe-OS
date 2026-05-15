import hashlib
import logging

class HSMPQCSigner:
    def __init__(self):
        logging.info("HSMPQCSigner initialized.")

    def sign_payload(self, payload: bytes) -> str:
        # Mock Post-Quantum Cryptographic signature (SHA3-256 + Dilithium-like)
        base_hash = hashlib.sha3_256(payload).hexdigest()
        # Append mock PQC Dilithium string
        pqc_sig = f"PQC-DILITHIUM-[{base_hash[:16]}]"
        return pqc_sig

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        expected = self.sign_payload(payload)
        return expected == signature
