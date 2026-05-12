use arkhe_entropy_oracle::shannon_entropy;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct RiskProfile {
    pub apy_mean: f64,
    pub apy_stdev: f64,
    pub entropy_30d: f64,   // bits de incerteza nos últimos 30 dias
    pub risk_level: RiskLevel,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum RiskLevel {
    Baixo,
    Moderado,
    Alto,
    Extremo,
}

pub fn to_bytes(pool_history: &[f64]) -> Vec<u8> {
    let mut bytes = Vec::new();
    for &val in pool_history {
        bytes.extend_from_slice(&val.to_be_bytes());
    }
    bytes
}

pub fn compute_risk(pool_history: &[f64]) -> RiskProfile {
    if pool_history.is_empty() {
        return RiskProfile {
            apy_mean: 0.0,
            apy_stdev: 0.0,
            entropy_30d: 0.0,
            risk_level: RiskLevel::Baixo,
        };
    }
    let apy_mean = pool_history.iter().sum::<f64>() / pool_history.len() as f64;
    let apy_stdev = (pool_history.iter().map(|v| (v - apy_mean).powi(2)).sum::<f64>()
        / pool_history.len() as f64).sqrt();

    let history_bytes = to_bytes(pool_history);
    let entropy = shannon_entropy(&history_bytes);

    let risk_level = if entropy < 2.0 { RiskLevel::Baixo }
                     else if entropy < 4.0 { RiskLevel::Moderado }
                     else if entropy < 6.0 { RiskLevel::Alto }
                     else { RiskLevel::Extremo };

    RiskProfile { apy_mean, apy_stdev, entropy_30d: entropy, risk_level }
}
