use crate::agent::SecurityError;
use crate::patch_verification::PatchProof;
use arkhe_temporal::TemporalChain;
use std::sync::Arc;

pub struct DaybreakAudit {
    chain: Arc<TemporalChain>,
}

impl DaybreakAudit {
    pub fn new(chain: Arc<TemporalChain>) -> Self {
        Self { chain }
    }

    /// Ancorar prova de patch na TemporalChain.
    pub async fn record_patch_verified(&self, proof: &PatchProof) -> Result<(), SecurityError> {
        let payload = serde_json::to_vec(&proof)?;
        // TODO: find how to actually add block, e.g. self.chain.add_block(&payload).await?;
        Ok(())
    }
}
