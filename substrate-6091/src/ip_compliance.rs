use serde::{Serialize, Deserialize};

pub struct BerneConventionAdapter;

impl BerneConventionAdapter {
    pub fn new(config: IPMultiversalConfig) -> Self {
        Self
    }

    pub fn validate_artwork(&self, fingerprint: &ArtFingerprint) -> Result<(), IPViolation> {
        Ok(())
    }
}

pub struct IPMultiversalConfig;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ArtFingerprint;

pub struct OrcidToCopyright;
pub struct IPMultiversalProof;

#[derive(Debug, thiserror::Error)]
pub enum IPViolation {
    #[error("IP compliance violation")]
    Violation,
}
