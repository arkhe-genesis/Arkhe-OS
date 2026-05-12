use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct MultiversalProof {
    pub hash: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ComplianceInfo {
    pub jurisdiction: String,
    pub compliant: bool,
    pub kyc_required: bool,
    pub proof: MultiversalProof,
}
