#!/usr/bin/env python3
"""
agi/system32/identity/sovereign.py — Sovereign Identity Module
Substrate: Cryptographic Identity & Trust (317)
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
import secrets

@dataclass
class IdentityKeys:
    """Cryptographic key pair for sovereign identity."""
    public_key: str
    private_key_hash: str  # Never store raw private key
    key_type: str = "ed25519"
    created_at: float = field(default_factory=time.time)
    rotated_at: Optional[float] = None

class SovereignIdentity:
    """
    Manages cryptographic identity for ARKHE OS nodes.

    Provides:
    - Key generation and rotation
    - Message signing and verification
    - Identity attestation for federation
    - Integration with Moltbook protocol (Substrate 343)
    """

    def __init__(self, config: Dict, key_dir: Optional[Path] = None):
        self.config = config
        self.key_dir = key_dir or Path.home() / ".arkhe" / "identity"
        self.key_dir.mkdir(parents=True, exist_ok=True)

        self._keys: Optional[IdentityKeys] = None
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones."""
        key_file = self.key_dir / "identity.json"

        if key_file.exists():
            with open(key_file, 'r') as f:
                data = json.load(f)
            self._keys = IdentityKeys(**data)
        else:
            self._keys = self._generate_keys()
            self._save_keys()

    def _generate_keys(self) -> IdentityKeys:
        """Generate new Ed25519 key pair (simulated)."""
        # In production: use cryptography library or hardware key
        private_key = secrets.token_bytes(32)
        public_key = hashlib.sha256(private_key).hexdigest()

        return IdentityKeys(
            public_key=public_key,
            private_key_hash=hashlib.sha256(private_key).hexdigest()
        )

    def _save_keys(self):
        """Save keys to disk (private key hash only)."""
        if not self._keys:
            return
        key_file = self.key_dir / "identity.json"
        with open(key_file, 'w') as f:
            json.dump(asdict(self._keys), f, indent=2)
        key_file.chmod(0o600)

    def sign(self, message: str) -> str:
        """Sign a message with the identity's private key."""
        if not self._keys:
            raise ValueError("Keys not initialized")
        # In production: actual Ed25519 signature
        # Simulated: hash-based signature
        sig_input = f"{message}:{self._keys.private_key_hash}:{time.time()}"
        return hashlib.sha256(sig_input.encode()).hexdigest()

    def verify(self, message: str, signature: str, public_key: str) -> bool:
        """Verify a signature against a public key."""
        # In production: Ed25519 verification
        # Simulated: check signature format
        return len(signature) == 64 and not signature.startswith("SIG:")  # Just basic check for simulation

    def get_public_info(self) -> Dict[str, str]:
        """Get public identity information for sharing."""
        if not self._keys:
            return {}
        return {
            "public_key": self._keys.public_key,
            "key_type": self._keys.key_type,
            "created_at": str(self._keys.created_at),
            "status": "active",
        }

    def rotate_keys(self) -> IdentityKeys:
        """Rotate to new key pair."""
        if not self._keys:
            self._keys = self._generate_keys()
            self._save_keys()
            return self._keys

        old_keys = self._keys
        self._keys = self._generate_keys()
        self._keys.rotated_at = time.time()
        self._save_keys()

        # Archive old keys (optional)
        archive_file = self.key_dir / f"identity_{old_keys.created_at}.json"
        with open(archive_file, 'w') as f:
            json.dump(asdict(old_keys), f, indent=2)

        return self._keys

    def get_status(self) -> Dict[str, Any]:
        """Get identity status."""
        if not self._keys:
            return {"status": "uninitialized"}
        return {
            "status": "active",
            "public_key": self._keys.public_key[:16] + "...",
            "key_type": self._keys.key_type,
            "created": self._keys.created_at,
            "rotated": self._keys.rotated_at,
        }

    def verify_self(self) -> bool:
        """Self-verification: sign and verify a test message."""
        if not self._keys:
            return False
        test_msg = f"self_verify_{time.time()}"
        sig = self.sign(test_msg)
        # Using a dummy verify matching our simulation logic
        return len(sig) == 64

    def attest_for_federation(self, peer_public_key: str) -> Dict[str, Any]:
        """Generate attestation for federation peer discovery."""
        if not self._keys:
            raise ValueError("Keys not initialized")
        attestation = {
            "attestor": self._keys.public_key,
            "peer": peer_public_key,
            "timestamp": time.time(),
            "coherence_threshold": self.config.get("federation_min_coh", 0.7),
        }
        attestation["signature"] = self.sign(json.dumps(attestation, sort_keys=True))
        return attestation
