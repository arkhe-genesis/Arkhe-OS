use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageToken {
    pub user_key: String, // Simplified as String for now
    pub vendor_id: String,
    pub timestamp: u64,
    pub feature_hash: [u8; 32],
    pub zk_proof: String, // Simplified as String for now
}
