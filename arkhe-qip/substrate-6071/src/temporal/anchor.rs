use sha3::{Sha3_256, Digest};
use blake3;
use tracing::{info, warn};
use serde::{Serialize, Deserialize};

use crate::types::TemporalBlock;
use crate::engine::TemporalChainInterface;

pub struct TemporalAnchor {
    endpoint: String,
}

impl TemporalAnchor {
    pub fn new(endpoint: &str) -> Self {
        Self {
            endpoint: endpoint.to_string(),
        }
    }
}
