use pacir_agi_core::{ArkheError, ArkheResult, GgufManifest};
pub async fn verify_rekor_anchor(m: &GgufManifest) -> ArkheResult<()> {
    let entry = m
        .arkhe_rekor_entry_id
        .as_deref()
        .ok_or_else(|| ArkheError::InvalidManifest("Rekor entry ID is absent".into()))?;
    let response = reqwest::Client::new()
        .get(format!(
            "https://rekor.sigstore.dev/api/v1/log/entries/{entry}"
        ))
        .send()
        .await
        .map_err(|e| ArkheError::NetworkError(e.to_string()))?;
    if response.status().is_success() {
        Ok(())
    } else {
        Err(ArkheError::VerificationFailed(format!(
            "Rekor entry was not found ({})",
            response.status()
        )))
    }
}
