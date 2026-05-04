use crate::core::config::SchedulerConfig;
use crate::core::orchestrator::{SharedState, MissionResult, ZoneStatus};
use anyhow::Result;
use std::sync::Arc;
use tokio::sync::RwLock;

pub struct StaticScheduler {
    config: SchedulerConfig,
}

pub struct StepResult {
    pub reward: f64,
}

impl StaticScheduler {
    pub fn new(config: &SchedulerConfig) -> Result<Self> {
        Ok(Self {
            config: config.clone(),
        })
    }

    pub async fn execute_step(
        &self,
        mission_def: &crate::core::config::MissionConfig,
        target_zones: &[String],
        shared_state: &Arc<RwLock<SharedState>>,
    ) -> Result<StepResult> {
        Ok(StepResult { reward: 0.0 })
    }
}
