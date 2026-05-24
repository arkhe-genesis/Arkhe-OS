//! Arkhe HyperCycle Module
//!
//! TODA/IP settlement and Node Factory

use crate::{ArkheError, GHOST, broadcast::DisputeControl};

/// Tilling engine trait
pub trait TillingEngine {
    fn compute_tilling(&self, uptime: f64, computations: f64, reputation: f64) -> f64;
}

/// Settlement engine trait
pub trait SettlementEngine {
    fn settle(&self, bounty_id: &str, amount: f64, tilling: f64) -> Result<Settlement, ArkheError>;
}

/// TODA/IP settlement
pub struct TODAIPSettlement;

impl SettlementEngine for TODAIPSettlement {
    fn settle(&self, bounty_id: &str, amount: f64, tilling: f64) -> Result<Settlement, ArkheError> {
        if tilling < GHOST {
            return Err(ArkheError::HyperCycleSettlementFailed(
                format!("Tilling {} < Ghost {}", tilling, GHOST)
            ));
        }

        Ok(Settlement {
            bounty_id: bounty_id.to_string(),
            amount,
            currency: "USDC".to_string(),
            protocol: "TODA/IP".to_string(),
            tilling,
        })
    }
}

/// Settlement record
#[derive(Debug, Clone)]
pub struct Settlement {
    pub bounty_id: String,
    pub amount: f64,
    pub currency: String,
    pub protocol: String,
    pub tilling: f64,
}

/// Node Factory
pub struct NodeFactory {
    _level: u8,
    _max_children: usize,
}

impl NodeFactory {
    pub fn new() -> Self {
        Self { _level: 10, _max_children: 2 }
    }
}


/// Dispute-aware settlement engine that rejects isolated nodes based on ∆*
pub struct DisputeAwareSettlement {
    pub inner: TODAIPSettlement,
    pub dispute_control: DisputeControl,
}

impl DisputeAwareSettlement {
    pub fn new(dispute_control: DisputeControl) -> Self {
        Self {
            inner: TODAIPSettlement,
            dispute_control,
        }
    }

    pub fn settle_with_dispute(
        &self,
        bounty_id: &str,
        amount: f64,
        tilling: f64,
        node_id: &str,
    ) -> Result<Settlement, ArkheError> {
        // If the node is isolated by Dispute Control, immediately reject
        if self.dispute_control.is_isolated(node_id) {
            return Err(ArkheError::HyperCycleSettlementFailed(
                format!("Node {} is isolated due to inconsistent results (∆*)", node_id)
            ));
        }

        self.inner.settle(bounty_id, amount, tilling)
    }
}
