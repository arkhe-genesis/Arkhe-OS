use pacir_agi_core::{ArkheError, ArkheResult, GgufManifest};
pub fn sanitize(m: &GgufManifest) -> ArkheResult<()> {
    if m.arkhe_version.is_empty() || m.manifest_type != GgufManifest::ROUTING_MANIFEST {
        return Err(ArkheError::InvalidManifest(
            "version or manifest type is invalid".into(),
        ));
    }
    if m.moe.total_experts == 0
        || m.moe.routing_table_hash.is_empty()
        || m.arkhe_identity.did.is_empty()
    {
        return Err(ArkheError::InvalidManifest(
            "required routing metadata is absent".into(),
        ));
    }
    if m.moe
        .expert_manifest
        .iter()
        .any(|e| e.cid.is_empty() || e.country.is_empty())
    {
        return Err(ArkheError::InvalidManifest(
            "expert CID or country is absent".into(),
        ));
    }
    Ok(())
}
