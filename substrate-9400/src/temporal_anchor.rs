use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubscriptionBlock {
    pub user_id: String,
    pub vendors: Vec<String>,
    pub monthly_fee: f64,
}

pub fn anchor_subscription(block: &SubscriptionBlock) -> bool {
    // In a real system this would anchor to TemporalChain
    true
}
