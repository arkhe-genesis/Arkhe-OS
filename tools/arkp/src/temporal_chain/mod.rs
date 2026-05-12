pub struct TemporalChainAnchor {
    pub chain_endpoint: String,
}

impl TemporalChainAnchor {
    pub fn new(endpoint: &str) -> Self {
        Self {
            chain_endpoint: endpoint.to_string(),
        }
    }

    pub fn anchor_execution(&self, state_hash: &str) {
        println!("Anchoring execution state {} to TemporalChain at {}", state_hash, self.chain_endpoint);
    }
}
