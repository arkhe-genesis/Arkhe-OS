from core.vault.vault_migration import PortableVaultContainer, MigrationCapabilityToken, VaultManifest, generate_migration_equivalence_proof
from core.vault.participant_vault import ParticipantDataVault

def test_vault_migration():
    manifest = VaultManifest("root_hash", "doc_hash", "state_hash")
    container = PortableVaultContainer(
        manifest=manifest,
        encrypted_blocks=[],
        merkle_root=b"root",
        zk_migration_proof=b"proof",
        migration_token_ref="ref"
    )
    proof = generate_migration_equivalence_proof("did:arkhe:123", {"state": "active"}, container)
    assert proof.statement == "vault_structural_equivalence"
