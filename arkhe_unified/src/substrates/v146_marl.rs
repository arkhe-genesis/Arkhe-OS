use anyhow::Result;

pub struct AsyncMARLAgent {}

impl AsyncMARLAgent {
    pub fn new(_zone: &str, _config: &serde_json::Value) -> Result<Self> {
        Ok(Self {})
    }
}
