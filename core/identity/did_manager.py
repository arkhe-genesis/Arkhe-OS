import hashlib
import base64
import json
from typing import Dict, Any, Tuple

class DIDManager:
    """Manages W3C Decentralized Identifiers (DID) anchored to participant root hashes."""

    def __init__(self, participant_root_hash: str):
        self.participant_root_hash = participant_root_hash
        self.did = f"did:arkhe:participant:{participant_root_hash}"

    def generate_jwk(self, public_key_bytes: bytes) -> Dict[str, Any]:
        """Generates a JSON Web Key (JWK) representation for a public key."""
        # This is a mock JWK generation for Ed25519
        encoded_key = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
        return {
            "kty": "OKP",
            "crv": "Ed25519",
            "x": encoded_key
        }

    def create_did_document(self, public_key_bytes: bytes, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generates the DID Document."""
        jwk = self.generate_jwk(public_key_bytes)
        key_id = f"{self.did}#key-1"

        doc = {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/arkhe/v1"
            ],
            "id": self.did,
            "verificationMethod": [{
                "id": key_id,
                "type": "JsonWebKey2020",
                "controller": self.did,
                "publicKeyJwk": jwk
            }],
            "authentication": [key_id],
            "service": [{
                "id": f"{self.did}#data-vault",
                "type": "ArkheDataVault",
                "serviceEndpoint": f"https://vault.arkhe.os/{self.participant_root_hash}"
            }]
        }

        if metadata:
            doc["arkhe:participantMetadata"] = {
                "rootHash": self.participant_root_hash,
                **metadata
            }

        return doc

    def generate_participant_root_hash(self, seed: bytes) -> str:
        """Helper to generate a root hash if not provided initially."""
        return hashlib.sha256(seed).hexdigest()
