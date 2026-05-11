use crate::zk_lib::ZKProof;
use crate::{RegulatoryConfig, VerificationReport, VerificationError};

/// Proof that the Carbon Twin adequately explored the conformation space.
pub struct CoherenceProof {
    pub merkle_root: [u8; 32],
    pub exploration_coverage: f64,  // fraction of space explored
    pub inner_zk: ZKProof,          // ZK proof that exploration is honest
    pub temporal_anchor: u64,       // block number of this proof
}

impl CoherenceProof {
    /// Verify the proof against the regulatory threshold (e.g., >99.9%).
    pub fn verify_for_regulator(
        &self,
        regulator_config: &RegulatoryConfig,
    ) -> Result<VerificationReport, VerificationError> {
        if self.exploration_coverage >= regulator_config.min_coverage {
            Ok(VerificationReport {
                message: format!("Coverage is {:.4}, minimum is {:.4}", self.exploration_coverage, regulator_config.min_coverage),
            })
        } else {
            Err(VerificationError(format!("Coverage is {:.4}, minimum is {:.4}", self.exploration_coverage, regulator_config.min_coverage)))
        }
    }
}
