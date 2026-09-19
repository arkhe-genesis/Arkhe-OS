pub mod gate_hash;
pub mod gate_rekor;
pub mod gate_sanitize;
pub mod gate_signature;
pub mod merkle;
use pacir_agi_core::{ArkheResult, GgufManifest};
/// Runs the five ordered validation gates. Rekor remains an online trust anchor.
pub async fn verify_manifest(manifest: &GgufManifest) -> ArkheResult<()> {
    gate_sanitize::sanitize(manifest)?;
    gate_hash::verify_hash(manifest)?;
    gate_signature::verify_hybrid_signature(manifest)?;
    gate_rekor::verify_rekor_anchor(manifest).await?;
    merkle::verify_merkle_proof(manifest)
}
