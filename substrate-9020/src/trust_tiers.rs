use crate::agent::SecurityError;

#[derive(Clone, Debug, PartialEq)]
pub enum KYCStatus {
    Verified,
    Unverified,
}

// Stub for missing OrcidProof
#[derive(Clone, Debug)]
pub struct OrcidProof;

#[derive(Clone, Debug)]
pub enum TrustTier {
    Default,               // acesso público com safeguard padrão
    TrustedCyber,           // defensor verificado (Trusted Access)
    CyberSpecialist,        // GPT-5.5-Cyber level: maior permissividade
}

pub struct TieredAccessControl {
    tier: TrustTier,
    orcid: Option<OrcidProof>,
    kyc: KYCStatus,
}

impl TieredAccessControl {
    pub fn authorize(&self, action: &str) -> Result<(), SecurityError> {
        match self.tier {
            TrustTier::Default => {
                if action.contains("patch") { Err(SecurityError::InsufficientTier) }
                else { Ok(()) }
            }
            TrustTier::TrustedCyber => {
                if self.kyc != KYCStatus::Verified { Err(SecurityError::InsufficientTier) }
                else { Ok(()) }
            }
            TrustTier::CyberSpecialist => Ok(()),
        }
    }
}
