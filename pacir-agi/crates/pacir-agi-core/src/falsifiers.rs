//! A `true` result means the corresponding conjecture has been falsified.
use crate::{brics::verify_brics_invariants, GgufManifest};
pub fn falsify_agi_01(m: &GgufManifest) -> bool {
    m.tensor_count() != 0
}
pub fn falsify_agi_02(ed25519_valid: bool, ml_dsa_valid: bool) -> bool {
    !(ed25519_valid && ml_dsa_valid)
}
pub fn falsify_agi_03(m: &GgufManifest) -> bool {
    m.arkhe_record_hash.as_deref() != Some(m.compute_hash_without_record().as_str())
}
pub fn falsify_agi_04(m: &GgufManifest) -> bool {
    verify_brics_invariants(m).is_err()
}
pub fn falsify_agi_05(m: &GgufManifest) -> bool {
    m.moe.routing_table_hash.is_empty()
}
pub fn falsify_agi_06(latency_ms: f64, target_ms: f64) -> bool {
    !latency_ms.is_finite() || latency_ms > target_ms
}
pub fn falsify_agi_07(_: f64) -> bool {
    true
}
pub fn falsify_agi_08(_: &str) -> bool {
    true
}
pub fn falsify_agi_09(experts: u64, demonstrated_max: u64) -> bool {
    experts > demonstrated_max
}
pub fn falsify_agi_10(rekor_entry_exists: bool) -> bool {
    !rekor_entry_exists
}
pub fn falsify_agi_11(local_resolution_works: bool) -> bool {
    !local_resolution_works
}
pub fn falsify_agi_12(gpus: u64, experts: u64) -> bool {
    gpus < experts.div_ceil(100)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn hybrid_requires_both() {
        assert!(!falsify_agi_02(true, true));
        assert!(falsify_agi_02(true, false));
    }
    #[test]
    fn permanently_falsified_are_true() {
        assert!(falsify_agi_07(1.));
        assert!(falsify_agi_08("WormGraph"));
    }
}
