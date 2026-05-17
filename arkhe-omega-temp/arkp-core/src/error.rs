
use thiserror::Error;
use serde::Serialize;

#[derive(Error, Debug, Serialize)]
pub enum ArkpError {
    #[error("[ARKP-CORE-001] IO error: {0}")]
    Io(String),
    #[error("[ARKP-CORE-002] Manifest parse error: {0}")]
    Manifest(String),
    #[error("[ARKP-CORE-003] Dependency resolution failed: {0}")]
    DepResolution(String),
    #[error("[ARKP-CORE-004] Build failed: {0}")]
    Build(String),
}
