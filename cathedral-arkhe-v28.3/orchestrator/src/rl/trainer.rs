use async_trait::async_trait;
use crate::rl::rollout_worker_debate::RolloutExperience;
use crate::rl::ledger_integration::ConsensusLedger;
use std::sync::Arc;

#[derive(Default)]
pub struct TrainerConfig {}

#[async_trait]
pub trait PolicyTrainer: Send + Sync {
    async fn update(&mut self, experiences: &[RolloutExperience]) -> Result<(), String>;
    fn current_version(&self) -> u64;
}

pub struct PpoGrpoTrainer {}
impl PpoGrpoTrainer {
    pub fn new(_config: TrainerConfig, _ledger: Option<Arc<dyn ConsensusLedger>>) -> Self {
        Self {}
    }
}
#[async_trait]
impl PolicyTrainer for PpoGrpoTrainer {
    async fn update(&mut self, _experiences: &[RolloutExperience]) -> Result<(), String> {
        Ok(())
    }
    fn current_version(&self) -> u64 {
        1
    }
}

pub fn create_trainer(_config: TrainerConfig, _ledger: Option<Arc<dyn ConsensusLedger>>) -> Box<dyn PolicyTrainer> {
    Box::new(PpoGrpoTrainer::new(_config, _ledger))
}
