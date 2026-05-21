#![cfg_attr(feature = "embedded", no_std)]

pub mod auth;
pub mod compute;
pub mod broadcast;
pub mod snom;
pub mod hypercycle;
pub mod gates;
pub mod partners;
pub mod octra_bridge;
pub mod bulletproof_access;

use serde::{Deserialize, Serialize};
use sha3::{Sha3_256, Digest};
use chrono::{DateTime, Utc};

/// Canonical constant: Ghost Invariant
pub const GHOST: f64 = 0.577_350_269_189_625_8;

/// Canonical constant: Loopseal Invariant
pub const LOOPSEAL: f64 = 0.349_065_850_398_865_9;

/// Canonical constant: Gap Sovereign Invariant
pub const GAP_SOVEREIGN: f64 = 0.999_9;

/// Partner identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PartnerId(pub String);

/// Session identifier (16-byte hex)
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SessionId(pub String);

/// Canonical seal (SHA3-256 hex)
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Seal(pub String);

/// Φ_C value with invariant bounds checking
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct PhiC(pub f64);

impl PhiC {
    pub fn new(value: f64) -> Result<Self, ArkheError> {
        if value <= GHOST {
            return Err(ArkheError::BelowGhost(value));
        }
        if value >= GAP_SOVEREIGN {
            return Err(ArkheError::AboveGap(value));
        }
        Ok(PhiC(value))
    }

    pub fn compute_workload(base: f64, complexity: f64, humility: f64) -> Result<Self, ArkheError> {
        let phi = base * (1.0 - complexity * 0.1) * (1.0 + humility * 0.1);
        let clamped = phi.max(GHOST).min(GAP_SOVEREIGN);
        Self::new(clamped)
    }
}

/// Humility score with Ghost validation
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct HumilityScore(pub f64);

impl HumilityScore {
    pub fn new(value: f64) -> Result<Self, ArkheError> {
        if value < GHOST {
            return Err(ArkheError::HumilityBelowGhost(value));
        }
        Ok(HumilityScore(value))
    }
}

/// Core error types
#[derive(Debug, thiserror::Error)]
pub enum ArkheError {
    #[error("Φ_C below Ghost: {0} < {GHOST}")]
    BelowGhost(f64),
    #[error("Φ_C above Gap: {0} > {GAP_SOVEREIGN}")]
    AboveGap(f64),
    #[error("Humility below Ghost: {0} < {GHOST}")]
    HumilityBelowGhost(f64),
    #[error("Partner not found: {0}")]
    PartnerNotFound(String),
    #[error("Invalid session: {0}")]
    InvalidSession(String),
    #[error("SNOM verification failed: {0}")]
    SNOMVerificationFailed(String),
    #[error("HyperCycle settlement failed: {0}")]
    HyperCycleSettlementFailed(String),
    #[error("Not implemented")]
    NotImplemented,
}

/// Generate canonical temporal seal
pub fn generate_seal(
    partner_id: &PartnerId,
    workload_type: &str,
    input_hash: &str,
    phi_c: PhiC,
    gate: &str,
    timestamp: DateTime<Utc>,
) -> Seal {
    let input = format!(
        "safecore_v2_{}_{}_{}_{:.6}_{}_{}",
        partner_id.0, workload_type, input_hash, phi_c.0, gate,
        timestamp.to_rfc3339()
    );
    let mut hasher = Sha3_256::new();
    hasher.update(input.as_bytes());
    let result = hasher.finalize();
    Seal(hex::encode(result))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ghost_invariant() {
        assert!((GHOST - std::f64::consts::SQRT_2 / 2.0).abs() > 0.01);
        assert!((GHOST * GHOST - 1.0/3.0).abs() < 1e-10);
    }

    #[test]
    fn test_loopseal_invariant() {
        assert!((LOOPSEAL - std::f64::consts::PI / 9.0).abs() < 1e-10);
    }

    #[test]
    fn test_phi_c_bounds() {
        assert!(PhiC::new(GHOST + 0.1).is_ok());
        assert!(PhiC::new(GHOST - 0.1).is_err());
        assert!(PhiC::new(GAP_SOVEREIGN + 0.1).is_err());
    }

    #[test]
    fn test_humility_bounds() {
        assert!(HumilityScore::new(GHOST + 0.1).is_ok());
        assert!(HumilityScore::new(GHOST - 0.1).is_err());
    }

    #[test]
    fn test_seal_determinism() {
        let partner = PartnerId("test".to_string());
        let phi = PhiC::new(0.8).unwrap();
        let t1 = Utc::now();
        let seal1 = generate_seal(&partner, "test", "hash", phi, "PG-NA", t1);
        let seal2 = generate_seal(&partner, "test", "hash", phi, "PG-NA", t1);
        assert_eq!(seal1.0, seal2.0);
    }
}
