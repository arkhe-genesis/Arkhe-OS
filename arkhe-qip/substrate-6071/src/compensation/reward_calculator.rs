use crate::types::{CompensationEvent, BlockValueInfo, SLATier};
use crate::errors::CompensationError;
use crate::config::CompensationConfig;
use tracing::info;

pub struct RewardCalculator {
    config: CompensationConfig,
}

impl RewardCalculator {
    pub fn new(config: CompensationConfig) -> Self {
        Self { config }
    }

    pub fn calculate(
        &self,
        probability: f64,
        reputation_weight: f64,
        block_value: &BlockValueInfo,
    ) -> u64 {
        let base_value = self.calculate_base_value(block_value);

        let raw_reward = probability
            .clamp(0.0, 1.0)
            * reputation_weight
            * base_value;

        let fee_percent = self.config.cashout_fee_percent / 100.0;
        let net_reward = raw_reward * (1.0 - fee_percent);

        let cents = (net_reward * 100.0).round() as u64;

        cents.max(self.config.min_cashout_cents)
    }

    fn calculate_base_value(&self, block: &BlockValueInfo) -> f64 {
        let compute_value = block.energy_cost_usd * 100.0;
        let token_value = block.token_count as f64 * block.token_value_usd * 100.0;
        let sla_bonus = self.sla_bonus(block.sla_tier);
        let request_value = block.request_count as f64 * 0.1 * 100.0;

        compute_value + token_value + sla_bonus + request_value
    }

    fn sla_bonus(&self, tier: SLATier) -> f64 {
        match tier {
            SLATier::Free => 0.0,
            SLATier::Basic => 50.0,
            SLATier::Professional => 150.0,
            SLATier::Enterprise => 500.0,
            SLATier::Research => 1000.0,
        }
    }
}
