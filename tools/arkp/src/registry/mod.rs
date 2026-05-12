use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ArtBlock {
    pub hash: String,
    pub proof: String,
    pub orcid: Option<String>,
    pub qip_address: Option<String>,
}

pub struct MinimalRegistry {
    pub endpoint: String,
}

impl MinimalRegistry {
    pub fn new(endpoint: &str) -> Self {
        Self {
            endpoint: endpoint.to_string(),
        }
    }

    pub fn anchor(&self, _block: &ArtBlock) {
        println!("Anchoring ArtBlock to registry at {}", self.endpoint);
    }
}
