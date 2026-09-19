use thiserror::Error;

#[derive(Error, Debug, Clone, PartialEq, Eq)]
pub enum ArkheError {
    #[error("invalid manifest: {0}")]
    InvalidManifest(String),
    #[error("invariant violated: {0}")]
    InvariantViolated(String),
    #[error("verification failed: {0}")]
    VerificationFailed(String),
    #[error("network error: {0}")]
    NetworkError(String),
    #[error("expert not found: {0}")]
    ExpertNotFound(String),
}
pub type ArkheResult<T> = Result<T, ArkheError>;
