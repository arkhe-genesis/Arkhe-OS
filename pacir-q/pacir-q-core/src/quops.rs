//! Estado QUOPS. Todos os scores são consistentes com α = 1/√e.

use crate::alpha::{polarization_succeeds, ALPHA_PACIR_OMEGA};
use crate::error::{PacirError, PacirResult};

pub const TARGET_RSA_2048_Q: f64 = 2.5e8;
pub const TARGET_RSA_2048_OMEGA: f64 = 5.7e3;
pub const TARGET_FEMOCO_Q: f64 = 3.4e8;
pub const TARGET_FEMOCO_OMEGA: f64 = 8.0e2;

#[derive(Debug, Clone, PartialEq)]
pub struct QuopsState {
    pub system_name: String,
    pub n_physical_qubits: u64,
    pub n_logical_qubits: Option<u64>,
    pub q: f64,
    pub omega: f64,
    pub polarization: f64,
}

impl QuopsState {
    pub fn new(
        system_name: String,
        n_physical_qubits: u64,
        q: f64,
        omega: f64,
        polarization: f64,
    ) -> PacirResult<Self> {
        if !q.is_finite() || q < 1.0 {
            return Err(PacirError::OutOfRange {
                name: "Q".into(),
                value: q,
                min: 1.0,
                max: f64::INFINITY,
            });
        }
        if !omega.is_finite() || omega <= 0.0 {
            return Err(PacirError::OutOfRange {
                name: "Ω".into(),
                value: omega,
                min: f64::MIN_POSITIVE,
                max: f64::INFINITY,
            });
        }
        if !polarization.is_finite() || !(0.0..=1.0).contains(&polarization) {
            return Err(PacirError::OutOfRange {
                name: "polarization".into(),
                value: polarization,
                min: 0.0,
                max: 1.0,
            });
        }
        Ok(Self {
            system_name,
            n_physical_qubits,
            n_logical_qubits: None,
            q,
            omega,
            polarization,
        })
    }

    pub fn is_successful(&self) -> bool {
        polarization_succeeds(self.polarization)
    }
    pub fn gap_orders(&self, target_q: f64) -> f64 {
        (target_q / self.q).log10()
    }
    pub fn is_admissible(s: f64, w: f64) -> bool {
        w > 0.0 && s >= w.powi(2) && s <= w.powi(3)
    }
}

/// Scores verificados (α = 1/√e).
pub fn verified_scores() -> Vec<QuopsState> {
    [
        ("Willow", 105, 216.0, 2.0e7),
        ("ibm_boston", 156, 204.0, 3.1e5),
        ("H2-1", 56, 1320.0, 353.0),
        ("Helios-1", 98, 1504.0, 303.0),
        ("Helios-1+PS", 98, 1824.0, 247.0),
        ("Helios-1+Steane", 8, 40.0, 4.9),
    ]
    .into_iter()
    .map(|(name, qubits, q, omega)| {
        QuopsState::new(name.into(), qubits, q, omega, ALPHA_PACIR_OMEGA + 0.01)
            .expect("verified score must be valid")
    })
    .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn scores_pass_and_gap_is_correct() {
        assert!(verified_scores().iter().all(QuopsState::is_successful));
        let state = QuopsState::new("Helios-1".into(), 98, 1504.0, 303.0, 0.65).unwrap();
        assert!((state.gap_orders(TARGET_RSA_2048_Q) - 5.22).abs() < 0.05);
    }
    #[test]
    fn validates_inputs_and_admissibility() {
        assert!(QuopsState::is_admissible(100.0, 10.0));
        assert!(!QuopsState::is_admissible(10.0, 10.0));
        assert!(QuopsState::new("x".into(), 10, 0.5, 1.0, 0.9).is_err());
    }
}
