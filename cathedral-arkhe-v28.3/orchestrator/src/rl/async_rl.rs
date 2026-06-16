//! Cathedral ARKHE v28.3 — Async RL Orchestrator (ASystem-like)
//! Coordena rollouts assíncronos usando o novo AsyncRolloutWorker com JoinSet e Debate Rewards.
//! Selo: CATHEDRAL-ARKHE-v28.3-ASYNC-RL-ORCHESTRATOR-2026-06-16

use std::sync::Arc;
use std::time::Duration;
use tokio::sync::{Mutex, RwLock};
use tokio::task::JoinHandle;
use tracing::{info, warn, error};

// use cathedral_agent::agent_loop::CathedralAgent;
// use cathedral_agent::orchestrator::{String, String};
use crate::rl::config::AsyncRLConfig;
use crate::rl::replay_buffer::ReplayBuffer;
use crate::rl::reward_model::RewardModel;
use crate::rl::debate_rewards::DebateConsensusRewardModel;
use crate::rl::rollout_worker_debate::{AsyncRolloutWorker, RolloutManager, RolloutExperience};
use crate::rl::trainer::{PolicyTrainer, create_trainer, TrainerConfig};
use crate::rl::curriculum::CurriculumManager;
use crate::rl::ledger_integration::ConsensusLedger;

/// Orquestrador de RL assíncrono — ASystem-like.
pub struct AsyncRLOrchestrator {
    config: AsyncRLConfig,
    buffer: Arc<ReplayBuffer>,
    reward_model: Arc<dyn RewardModel>,
    debate_reward_model: Option<Arc<DebateConsensusRewardModel>>,
    agent: Arc<Mutex<dyn core::any::Any + Send + Sync>>,
    rollout_manager: Arc<Mutex<RolloutManager>>,
    policy_version: Arc<RwLock<u64>>,
    trainer_handle: Option<JoinHandle<()>>,
    running: Arc<RwLock<bool>>,
    trainer: Arc<Mutex<Box<dyn PolicyTrainer>>>,
    curriculum: Arc<Mutex<CurriculumManager>>,
    consensus_ledger: Option<Arc<dyn ConsensusLedger>>,
}

impl AsyncRLOrchestrator {
    /// Cria um novo orquestrador. Usa o worker de debate por padrão se o modelo de debate for fornecido.
    pub fn new(
        config: AsyncRLConfig,
        agent: Arc<Mutex<dyn core::any::Any + Send + Sync>>,
        buffer: Arc<ReplayBuffer>,
        reward_model: Arc<dyn RewardModel>,
        debate_reward_model: Option<Arc<DebateConsensusRewardModel>>,
        ledger: Option<Arc<dyn ConsensusLedger>>,
    ) -> Self {
        let trainer_config = TrainerConfig::default();
        let trainer = create_trainer(trainer_config, ledger.clone());
        let curriculum = Arc::new(Mutex::new(CurriculumManager::new()));

        let manager = RolloutManager::new(
            agent.clone(),
            buffer.clone(),
            reward_model.clone(),
            debate_reward_model.clone(),
            config.clone(),
        );

        Self {
            config: config.clone(),
            buffer,
            reward_model,
            debate_reward_model,
            agent,
            rollout_manager: Arc::new(Mutex::new(manager)),
            policy_version: Arc::new(RwLock::new(1)),
            trainer_handle: None,
            running: Arc::new(RwLock::new(false)),
            trainer: Arc::new(Mutex::new(trainer)),
            curriculum,
            consensus_ledger: ledger,
        }
    }

    /// Inicia o loop de treino assíncrono e os workers.
    pub async fn start(&mut self, initial_goals: Vec<String>) -> Result<(), String> {
        let mut running = self.running.write().await;
        if *running {
            return Err("Orchestrator already running".to_string());
        }
        *running = true;
        drop(running);

        let buffer = self.buffer.clone();
        let config = self.config.clone();
        let policy_version = self.policy_version.clone();
        let running_flag = self.running.clone();
        let trainer_arc = self.trainer.clone();

        *policy_version.write().await = 1;

        let trainer_handle = tokio::spawn(async move {
            let mut step = 0;
            while *running_flag.read().await {
                tokio::time::sleep(Duration::from_secs(config.train_interval_secs)).await;

                let current_version = *policy_version.read().await;
                let batch = buffer.sample_batch(config.batch_size, current_version).await;
                if !batch.is_empty() {
                    let mut trainer = trainer_arc.lock().await;
                    if let Err(e) = trainer.update(&batch).await {
                        warn!("Trainer update failed: {}", e);
                    }
                    let new_version = trainer.current_version();
                    *policy_version.write().await = new_version;
                    buffer.update_policy_version(new_version).await;
                }
                step += 1;
            }
        });
        self.trainer_handle = Some(trainer_handle);

        let goals = if initial_goals.is_empty() {
            let curriculum = self.curriculum.lock().await;
            let dummy_agent = "oracle".to_string();
            let task = curriculum.sample_task_for_agent(&dummy_agent).await;
            vec![task.description]
        } else {
            initial_goals
        };

        let mut manager = self.rollout_manager.lock().await;
        let token_budget = self.config.token_budget_per_rollout;
        let max_steps = self.config.max_steps_per_rollout;

        let results = manager.run_parallel_rollouts(goals, token_budget, max_steps).await
            .map_err(|e| format!("Rollout execution failed: {}", e))?;

        let total_experiences: usize = results.iter().map(|v| v.len()).sum();
        info!(
            target: "cathedral::async_rl",
            total_experiences,
            workers = config.num_rollout_workers,
            "Rollouts iniciais concluídos"
        );

        Ok(())
    }

    pub async fn run_additional_rollout(&self, goal: String) -> Result<Vec<RolloutExperience>, String> {
        let mut manager = self.rollout_manager.lock().await;
        let token_budget = self.config.token_budget_per_rollout;
        let max_steps = self.config.max_steps_per_rollout;

        let results = manager.run_parallel_rollouts(vec![goal], token_budget, max_steps).await
            .map_err(|e| format!("Rollout execution failed: {}", e))?;

        Ok(results.into_iter().next().unwrap_or_default())
    }

    pub async fn update_policy_version(&self, version: u64) {
        let manager = self.rollout_manager.lock().await;
        manager.update_all_policy_versions(version).await;
        *self.policy_version.write().await = version;
    }

    pub async fn get_worker_stats(&self) -> Vec<crate::rl::rollout_worker_debate::RolloutStats> {
        let manager = self.rollout_manager.lock().await;
        manager.all_stats().await
    }

    pub async fn shutdown(&mut self) {
        let mut running = self.running.write().await;
        if !*running {
            return;
        }
        *running = false;
        drop(running);

        if let Some(handle) = self.trainer_handle.take() {
            handle.abort();
        }
        info!("AsyncRLOrchestrator: shutdown completo.");
    }
}
