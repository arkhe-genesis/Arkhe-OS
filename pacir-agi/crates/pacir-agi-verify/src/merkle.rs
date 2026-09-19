use pacir_agi_core::{ArkheError, ArkheResult, GgufManifest};
/// A manifest leaf must be sealed before it can be included in an anchored Merkle tree.
pub fn verify_merkle_proof(m: &GgufManifest) -> ArkheResult<()> {
    if m.arkhe_record_hash.is_some() {
        Ok(())
    } else {
        Err(ArkheError::VerificationFailed(
            "Merkle leaf hash is absent".into(),
        ))
    }
}
