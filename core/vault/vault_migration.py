from dataclasses import dataclass
from typing import Tuple, List, Optional, Any
from datetime import datetime
import hashlib
from core.vault.participant_vault import ParticipantDataVault

@dataclass
class MigrationCapabilityToken:
    """Hardware-attested, time-bound authorization for vault relocation."""
    participant_did: str
    source_platform_id: str
    target_platform_id: str
    validity_window: Tuple[datetime, datetime]
    participant_hardware_signature: bytes  # Secure enclave/biometric signature
    migration_token_hash: str
    revocation_proof: Optional[str]  # Pre-signed revocation capability

@dataclass
class VaultManifest:
    hash_chain_root: str
    did_doc_hash: str
    consent_state_hash: str

@dataclass
class PortableVaultContainer:
    """Encrypted, verifiable vault package for cross-platform transfer."""
    manifest: VaultManifest  # Schema versions, DID doc hash, VC list, hash chain root
    encrypted_blocks: List[bytes]  # PQ-encrypted vault data, structured for parallel decryption
    merkle_root: bytes  # Root of Merkle tree over encrypted blocks
    zk_migration_proof: bytes  # ZK proof that structure matches participant's active vault
    migration_token_ref: str  # Reference to signed MigrationCapabilityToken


class MerkleTree:
    def __init__(self, root: bytes):
        self.root = root

def build_merkle_tree(leaves: List[Any]) -> MerkleTree:
    # A mock implementation for the tree
    hashed_leaves = [hashlib.sha256(leaf if isinstance(leaf, bytes) else str(leaf).encode()).digest() for leaf in leaves]
    combined = b"".join(hashed_leaves)
    return MerkleTree(root=hashlib.sha256(combined).digest())

class ZKProof:
    def __init__(self, statement: str, proof_bytes: bytes):
        self.statement = statement
        self.proof_bytes = proof_bytes

def generate_snark_proof(statement: str, public_inputs: list, witness: Any) -> ZKProof:
    # A mock implementation
    return ZKProof(statement=statement, proof_bytes=b"zk_proof_stub")

def generate_migration_equivalence_proof(participant_did: str,
                                         active_vault_state: Any,
                                         container: PortableVaultContainer) -> ZKProof:
    """
    Proves that the container is structurally identical to the active vault
    without revealing contents, hash chain, or consent state.
    """
    # Merkle tree over encrypted blocks, DID docs, VCs, hash chain root
    merkle_tree = build_merkle_tree([
        container.manifest.hash_chain_root,
        container.manifest.did_doc_hash,
        container.manifest.consent_state_hash,
        container.merkle_root
    ])

    # ZK proof: "I know a valid vault with merkle_root X that matches participant DID Y"
    return generate_snark_proof(
        statement="vault_structural_equivalence",
        public_inputs=[participant_did, merkle_tree.root],
        witness=active_vault_state
    )
