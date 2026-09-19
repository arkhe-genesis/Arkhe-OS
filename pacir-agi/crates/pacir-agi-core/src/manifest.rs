//! Serializable routing-manifest format. It deliberately carries no model tensors.
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ExpertEntry {
    pub index: u64,
    pub cid: String,
    pub country: String,
    pub size_bytes: u64,
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MoeConfig {
    pub total_experts: u64,
    pub active_experts_per_token: u32,
    pub routing_table_hash: String,
    pub expert_manifest: Vec<ExpertEntry>,
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct BricsGovernance {
    pub quorum_standard: String,
    pub quorum_critical: String,
    pub timelock_seconds: u64,
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct HybridSignature {
    pub ed25519: String,
    pub ml_dsa_65: String,
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ArkheIdentity {
    pub did: String,
    pub signature: HybridSignature,
}
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GgufManifest {
    pub arkhe_version: String,
    pub manifest_type: String,
    pub moe: MoeConfig,
    pub brics_governance: BricsGovernance,
    pub brics_invariants: Vec<String>,
    pub arkhe_identity: ArkheIdentity,
    pub arkhe_rekor_entry_id: Option<String>,
    pub arkhe_record_hash: Option<String>,
}
impl GgufManifest {
    pub const ROUTING_MANIFEST: &'static str = "routing_manifest";
    pub fn tensor_count(&self) -> u64 {
        0
    }
    /// Hashes a canonical JSON representation with the self-referential field omitted.
    pub fn compute_hash_without_record(&self) -> String {
        let mut copy = self.clone();
        copy.arkhe_record_hash = None;
        let json = serde_json::to_vec(&copy).expect("manifest serialization cannot fail");
        blake3::hash(&json).to_hex().to_string()
    }
    pub fn seal(&mut self) {
        self.arkhe_record_hash = Some(self.compute_hash_without_record());
    }
}
