use serde::{Deserialize, Serialize};

pub struct FinancialMultiversalBridge;

impl FinancialMultiversalBridge {
    pub fn new(config: FinancialMultiversalConfig) -> Self {
        Self
    }

    pub fn validate_transaction(&self, tx: &PixTransaction) -> Result<(), FinancialViolation> {
        Ok(())
    }
}

pub struct FinancialMultiversalConfig;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PixTransaction;

pub struct PixToSepa;
pub struct FedNowToPix;
pub struct CrossBorderCompliance;

#[derive(Debug, thiserror::Error)]
pub enum FinancialViolation {
    #[error("Financial compliance violation")]
    Violation,
}
