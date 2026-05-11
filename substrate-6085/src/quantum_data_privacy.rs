use serde::{Deserialize, Serialize};

pub struct DataPrivacyProver;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QMLPrivacyProof {
    pub dataset_hash: [u8; 32],
    pub epsilon: f64,
}
