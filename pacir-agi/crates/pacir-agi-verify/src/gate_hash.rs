use pacir_agi_core::{ArkheError, ArkheResult, GgufManifest};
pub fn verify_hash(m: &GgufManifest) -> ArkheResult<()> {
    match &m.arkhe_record_hash {
        Some(expected) if expected == &m.compute_hash_without_record() => Ok(()),
        Some(_) => Err(ArkheError::VerificationFailed(
            "BLAKE3 record hash mismatch".into(),
        )),
        None => Err(ArkheError::InvalidManifest("record hash is absent".into())),
    }
}
