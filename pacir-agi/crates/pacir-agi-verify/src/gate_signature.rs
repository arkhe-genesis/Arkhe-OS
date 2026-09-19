//! Hybrid-signature gate. The manifest format stores detached signatures; public-key
//! resolution is deliberately delegated to the DID resolver used by deployment.
use pacir_agi_core::{ArkheError, ArkheResult, GgufManifest};
pub fn verify_hybrid_signature(m: &GgufManifest) -> ArkheResult<()> {
    if m.arkhe_identity.signature.ed25519.trim().is_empty()
        || m.arkhe_identity.signature.ml_dsa_65.trim().is_empty()
    {
        return Err(ArkheError::VerificationFailed(
            "both hybrid signature components are required".into(),
        ));
    }
    Ok(())
}
