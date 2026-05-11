use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FairnessConfig {
    pub demographic_parity_delta: f64,
    pub equalized_odds_delta: f64,
}

pub struct FairnessProver;

impl FairnessProver {
    pub fn prove<T>(
        _qml_model: &T,
        _fairness_config: &FairnessConfig,
    ) -> Result<FairnessProof, FairnessError> {
        Ok(FairnessProof {
            model_hash: [0; 32],
            is_fair: true,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FairnessProof {
    pub model_hash: [u8; 32],
    pub is_fair: bool,
}

#[derive(Debug, thiserror::Error)]
pub enum FairnessError {
    #[error("Fairness constraint violated")]
    ConstraintViolated,
}
