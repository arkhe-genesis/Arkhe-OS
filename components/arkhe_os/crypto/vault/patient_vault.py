"""
Substrate 287: Patient-Controlled Data Vault
Redox data vault controlled by the patient via personal keys,
with sharing granularity and an immutable audit trail.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

@dataclass
class AuditRecord:
    timestamp: str
    action: str
    accessed_by: str
    data_reference: str
    proof_hash: str

class RedoxDataVault:
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.encrypted_data_store: Dict[str, bytes] = {}
        self.access_grants: Dict[str, List[str]] = {} # data_id -> list of authorized entities
        self.audit_trail: List[AuditRecord] = []

    def _hash_data(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def _derive_key(self, password: str) -> bytes:
        # In a real system, this would use Argon2 or PBKDF2 with a salt
        # For simplicity, we just hash the password to 32 bytes
        return hashlib.sha256(password.encode()).digest()

    def store_data(self, data_id: str, plain_data: dict, patient_password: str):
        """Encrypts and stores redox data using the patient's password."""
        key = self._derive_key(patient_password)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)

        serialized = json.dumps(plain_data).encode('utf-8')
        ciphertext = aesgcm.encrypt(nonce, serialized, None)

        # Store nonce + ciphertext
        self.encrypted_data_store[data_id] = nonce + ciphertext
        self.access_grants[data_id] = [self.patient_id] # Owner has access

        self._log_audit("STORE", self.patient_id, data_id)

    def grant_access(self, data_id: str, entity_id: str, patient_password: str):
        """Grants fine-grained access to a specific entity."""
        if data_id in self.access_grants:
            # Verify owner by attempting to decrypt
            try:
                self.retrieve_data(data_id, self.patient_id, patient_password)
                if entity_id not in self.access_grants[data_id]:
                    self.access_grants[data_id].append(entity_id)
                    self._log_audit("GRANT_ACCESS", entity_id, data_id)
            except Exception:
                pass # Fail silently or raise error

    def retrieve_data(self, data_id: str, accessing_entity: str, decryption_password: str) -> Optional[dict]:
        """Retrieves and decrypts data if authorized."""
        if data_id not in self.encrypted_data_store:
            return None

        if accessing_entity not in self.access_grants.get(data_id, []):
            self._log_audit("DENIED_ACCESS", accessing_entity, data_id)
            raise PermissionError(f"Entity {accessing_entity} not authorized for {data_id}")

        encrypted_data = self.encrypted_data_store[data_id]
        key = self._derive_key(decryption_password)
        aesgcm = AESGCM(key)

        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        try:
            plain_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            plain_str = plain_bytes.decode('utf-8')
            self._log_audit("RETRIEVE", accessing_entity, data_id)
            return json.loads(plain_str)
        except InvalidTag:
            self._log_audit("FAILED_DECRYPTION", accessing_entity, data_id)
            raise ValueError("Invalid decryption key")

    def _log_audit(self, action: str, entity: str, data_id: str):
        """Creates an immutable audit record."""
        timestamp = datetime.now().isoformat()

        # In a real system, the proof_hash would chain with the previous audit record's hash
        prev_hash = self.audit_trail[-1].proof_hash if self.audit_trail else "genesis"
        raw_string = f"{prev_hash}{timestamp}{action}{entity}{data_id}"
        proof_hash = self._hash_data(raw_string)

        record = AuditRecord(
            timestamp=timestamp,
            action=action,
            accessed_by=entity,
            data_reference=data_id,
            proof_hash=proof_hash
        )
        self.audit_trail.append(record)

    def get_audit_trail(self) -> List[AuditRecord]:
        return self.audit_trail
