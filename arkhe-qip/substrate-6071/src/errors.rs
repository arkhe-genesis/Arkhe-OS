// ============================================================================
// ARKHE QIP — Error Types
// ============================================================================

use thiserror::Error;
use crate::types::{DataFingerprint, TemporalBlock};

#[derive(Debug, Error)]
pub enum QipError {
    #[error("Temporal chain error: {0}")]
    TemporalError(String),

    #[error("Influence calculation failed: {0}")]
    InfluenceError(String),

    #[error("ZK proof generation failed: {0}")]
    ZkProofError(String),

    #[error("ZK proof verification failed: {0}")]
    ZkVerificationError(String),

    #[error("Payment processing error: {0}")]
    PaymentError(String),

    #[error("Oracle query failed: {0}")]
    OracleError(String),

    #[error("Data not found: fingerprint={0}")]
    DataNotFound(String),

    #[error("Invalid configuration: {0}")]
    ConfigError(String),

    #[error("Crypto error: {0}")]
    CryptoError(String),

    #[error("Serialization error: {0}")]
    SerializationError(String),

    #[error("Timeout: {0}")]
    Timeout(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Channel error: {0}")]
    ChannelError(String),

    #[error("Insufficient reputation: required {required}, actual {actual}")]
    InsufficientReputation { required: f64, actual: f64 },

    #[error("Duplicate compensation event: {0}")]
    DuplicateEvent(String),
}

#[derive(Debug, Error)]
pub enum InfluenceError {
    #[error("Invalid fingerprint: {0}")]
    InvalidFingerprint(String),

    #[error("Shard data unavailable: {0}")]
    ShardUnavailable(u32),

    #[error("Computation overflow")]
    Overflow,

    #[error("Insufficient samples")]
    InsufficientSamples,

    #[error("Convergence not reached after {0} iterations")]
    ConvergenceFailure(usize),
}

#[derive(Debug, Error)]
pub enum CompensationError {
    #[error("Invalid block: {0}")]
    InvalidBlock(String),

    #[error("Wallet not found for ORCID: {0}")]
    WalletNotFound(String),

    #[error("Amount below minimum threshold")]
    BelowMinimum,

    #[error("Duplicate payment")]
    DuplicatePayment,

    #[error("Escrow error: {0}")]
    EscrowError(String),
}
