use crate::invariants::GHOST;
use crate::humility::HumilityVerdict;
use sha3::{Sha3_256, Digest};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone)]
pub struct PaymentCommitment {
    pub task_id: String,
    pub payer: String,
    pub payee: String,
    pub amount_usdc: f64,
    pub protocol: String,        // "TODA/IP"
    pub settled_at: DateTime<Utc>,
    pub humility_at_settlement: f64,
}

pub struct TodaIpSettlement;

impl TodaIpSettlement {
    pub fn settle(
        task_id: &str, payer: &str, payee: &str, amount: f64,
        humility: &HumilityVerdict, tilling_score: f64,
    ) -> Result<PaymentCommitment, String> {
        // Guarda: humildade epistêmica
        match humility {
            HumilityVerdict::Acceptable { score } if *score >= GHOST => {},
            HumilityVerdict::Rejected { score, reason } => {
                return Err(format!("Humility check failed: {}", reason));
            }
            _ => return Err("Humility below Ghost".to_string()),
        }

        // Guarda: Tilling mínimo
        if tilling_score < GHOST {
            return Err(format!(
                "Tilling {:.4} < Ghost {:.4}", tilling_score, GHOST
            ));
        }

        let commitment = PaymentCommitment {
            task_id: task_id.to_string(),
            payer: payer.to_string(),
            payee: payee.to_string(),
            amount_usdc: amount,
            protocol: "TODA/IP".to_string(),
            settled_at: Utc::now(),
            humility_at_settlement: match humility {
                HumilityVerdict::Acceptable { score } => *score,
                _ => 0.0,
            },
        };

        Ok(commitment)
    }

    pub fn compute_settlement_hash(commitment: &PaymentCommitment) -> String {
        let input = format!("{}:{}:{}:{}:{}:{}:{}:{}",
            commitment.task_id.len(), commitment.task_id,
            commitment.payer.len(), commitment.payer,
            commitment.payee.len(), commitment.payee,
            commitment.amount_usdc, commitment.settled_at.to_rfc3339());
        hex::encode(Sha3_256::digest(input.as_bytes()))
    }
}