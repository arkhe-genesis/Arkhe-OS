use crate::export_control::WassenaarCircuitProof;
use crate::quantum_fairness::FairnessProof;

pub struct QuantumAuditTrail;

impl QuantumAuditTrail {
    pub fn anchor(
        _export_proof: &WassenaarCircuitProof,
        _fairness_proof: &FairnessProof,
    ) -> Result<(), AuditError> {
        Ok(())
    }
}

#[derive(Debug, thiserror::Error)]
pub enum AuditError {
    #[error("Anchor failed")]
    AnchorFailed,
}
