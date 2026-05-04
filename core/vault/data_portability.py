import json
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from core.vault.participant_vault import ParticipantDataVault, ParticipantKeyHierarchy, EncryptedVaultEntry

# Mock functions for signature and validation
def sign_export_package(package_hash: str, master_secret: bytes) -> str:
    return f"signature_of_{package_hash}"

def verify_export_package_signature(package_hash: str, signature: str, root_hash: str) -> bool:
    return signature == f"signature_of_{package_hash}"

@dataclass
class VaultExportPackage:
    """A transportable, encrypted package containing the participant's data vault."""
    participant_root_hash: str
    target_platform_did: str
    encrypted_entries: List[EncryptedVaultEntry]
    export_timestamp: float

    # Cryptographic integrity and provenance
    package_hash: str
    participant_signature: str

class DataPortabilityManager:
    """Manages exporting and importing of participant vaults between platforms."""

    @staticmethod
    def export_vault_to_platform(vault: ParticipantDataVault, participant_keys: ParticipantKeyHierarchy, target_platform_did: str) -> VaultExportPackage:
        """Packages the vault into a transportable format bound to a specific target platform."""
        import time

        # Serialize and package entries
        encrypted_entries = vault.entries.copy()

        # In a real system, we might re-encrypt the outer layer for the target platform's public key
        # to ensure it can only be processed there, but the inner encryption remains tied to participant keys.

        export_timestamp = time.time()

        # Compute package hash
        hash_input = f"{participant_keys.root_hash}:{target_platform_did}:{len(encrypted_entries)}:{export_timestamp}".encode()
        package_hash = hashlib.sha256(hash_input).hexdigest()

        # Sign the export with the participant's master secret (or derived signing key)
        participant_signature = sign_export_package(package_hash, participant_keys.master_secret)

        return VaultExportPackage(
            participant_root_hash=participant_keys.root_hash,
            target_platform_did=target_platform_did,
            encrypted_entries=encrypted_entries,
            export_timestamp=export_timestamp,
            package_hash=package_hash,
            participant_signature=participant_signature
        )

    @staticmethod
    def import_vault_from_platform(export_package: VaultExportPackage, participant_keys: ParticipantKeyHierarchy) -> ParticipantDataVault:
        """Securely unwraps and integrates an imported vault, validating signatures and restoring state."""

        # Verify the package belongs to this participant
        if export_package.participant_root_hash != participant_keys.root_hash:
            raise ValueError("Import failed: Vault root hash mismatch. This vault belongs to a different participant.")

        # Verify package integrity and origin
        if not verify_export_package_signature(export_package.package_hash, export_package.participant_signature, export_package.participant_root_hash):
            raise ValueError("Import failed: Invalid participant signature on export package.")

        # Reconstruct the vault
        imported_vault = ParticipantDataVault()
        imported_vault.entries = export_package.encrypted_entries.copy()

        # State hashes and hash chain are preserved from the original platform.
        # Additional checks can verify the hash chain integrity here.

        return imported_vault
