use crate::{ArkheError, ArkheResult, GgufManifest};
use std::collections::HashMap;
pub const TOTAL_EXPERTS: u64 = 250_000;
pub const MAX_ACTIVATION_PCT: f64 = 0.0016;
pub const MAX_COUNTRY_SHARE: f64 = 0.50;
pub const QUORUM_STANDARD: &str = "4/7";
pub const QUORUM_CRITICAL: &str = "5/7";
pub fn verify_brics_invariants(manifest: &GgufManifest) -> ArkheResult<()> {
    if manifest.moe.total_experts != TOTAL_EXPERTS {
        return Err(ArkheError::InvariantViolated(
            "INV-BRICS-01 total_experts must be 250000".into(),
        ));
    }
    let activation =
        manifest.moe.active_experts_per_token as f64 / manifest.moe.total_experts as f64 * 100.0;
    if activation > MAX_ACTIVATION_PCT {
        return Err(ArkheError::InvariantViolated(
            "INV-BRICS-02 activation limit exceeded".into(),
        ));
    }
    if manifest.brics_governance.quorum_standard != QUORUM_STANDARD
        || manifest.brics_governance.quorum_critical != QUORUM_CRITICAL
    {
        return Err(ArkheError::InvariantViolated(
            "INV-BRICS-05 quorum mismatch".into(),
        ));
    }
    let mut counts = HashMap::new();
    for e in &manifest.moe.expert_manifest {
        *counts.entry(&e.country).or_insert(0u64) += 1;
    }
    if counts
        .values()
        .any(|&n| n as f64 / manifest.moe.total_experts as f64 > MAX_COUNTRY_SHARE)
    {
        return Err(ArkheError::InvariantViolated(
            "INV-BRICS-04 country share exceeded".into(),
        ));
    }
    Ok(())
}
