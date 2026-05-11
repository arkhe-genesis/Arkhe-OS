pub struct ProofVerifier;
pub struct VerificationResult;
#[derive(Debug, thiserror::Error)]
pub enum VerificationError {
    #[error("Verification error")]
    Error,
}
pub struct BatchVerifier;
pub struct UniversalVerifier;
