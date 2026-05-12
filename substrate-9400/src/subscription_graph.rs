use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubscriptionGraph {
    pub users: Vec<String>,
    pub vendors: Vec<String>,
}

impl SubscriptionGraph {
    pub fn new() -> Self {
        Self {
            users: Vec::new(),
            vendors: Vec::new(),
        }
    }
}
