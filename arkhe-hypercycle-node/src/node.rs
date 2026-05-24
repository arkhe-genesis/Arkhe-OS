use crate::invariants::{GHOST, PHI};
use crate::tilling::TillingEngine;
use crate::humility::EpistemicHumilityEngine;
use crate::settlement::{TodaIpSettlement, PaymentCommitment};
use chrono::Utc;

pub struct ArkheHyperCycleNode {
    pub node_id: String,
    pub node_type: NodeType,
    pub owner_orcid: String,
    pub tilling: TillingEngine,
    pub transactions_settled: u64,
    pub phi_c: f64,
}

pub enum NodeType {
    NetworkNode { parent_gate: String, level: u8 },
    BoundaryNode { gate_id: String, level: u8 },
}

impl ArkheHyperCycleNode {
    pub fn new(id: String, node_type: NodeType, orcid: String) -> Self {
        Self {
            node_id: id,
            node_type,
            owner_orcid: orcid,
            tilling: TillingEngine::new(0.5, Utc::now()),
            transactions_settled: 0,
            phi_c: GHOST * PHI / 2.0,  // Φ_C inicial
        }
    }

    pub fn execute_task(&mut self, task_id: &str, complexity: f64,
                        task_type: &str, has_attestation: bool) -> Result<String, String> {
        let humility = EpistemicHumilityEngine::evaluate(
            complexity, task_type, has_attestation);

        match &humility {
            crate::humility::HumilityVerdict::Acceptable { score } => {
                let attestation = EpistemicHumilityEngine::compute_attestation(
                    task_id, &self.node_id, &task_id, *score);
                self.tilling.record_activity(10.0, 1, 0, 0);
                Ok(attestation)
            }
            crate::humility::HumilityVerdict::Rejected { reason, .. } => {
                Err(reason.clone())
            }
        }
    }

    pub fn settle(&mut self, task_id: &str, payer: &str, payee: &str,
                  amount: f64, complexity: f64, task_type: &str)
                  -> Result<PaymentCommitment, String> {
        let humility = EpistemicHumilityEngine::evaluate(
            complexity, task_type, true);
        let tilling = self.tilling.compute();

        let result = TodaIpSettlement::settle(
            task_id, payer, payee, amount, &humility, tilling.score)?;

        self.transactions_settled += 1;
        self.tilling.record_activity(5.0, 0, 1, 0);
        Ok(result)
    }
}