//! Arkhe Authentication Module
//!
//! Implements Ghost, Loopseal, and Gap invariant checks

use async_trait::async_trait;
use crate::{ArkheError, GHOST, LOOPSEAL, GAP_SOVEREIGN, HumilityScore, PhiC, PartnerId, SessionId};
use sha3::{Sha3_256, Digest};
use chrono::Utc;

/// Authentication trait for partners
#[async_trait]
pub trait Authenticator: Send + Sync {
    async fn authenticate(
        &self,
        partner_id: &PartnerId,
        orcid: &str,
        humility: HumilityScore,
    ) -> Result<AuthResult, ArkheError>;
}

/// Authentication result
#[derive(Debug, Clone)]
pub struct AuthResult {
    pub partner_id: PartnerId,
    pub session_id: SessionId,
    pub phi_c_base: PhiC,
    pub humility: HumilityScore,
    pub authenticated_at: chrono::DateTime<Utc>,
}

/// Ghost-based authenticator
pub struct GhostAuthenticator;

#[async_trait]
impl Authenticator for GhostAuthenticator {
    async fn authenticate(
        &self,
        partner_id: &PartnerId,
        orcid: &str,
        humility: HumilityScore,
    ) -> Result<AuthResult, ArkheError> {
        if humility.0 < GHOST {
            return Err(ArkheError::HumilityBelowGhost(humility.0));
        }

        let input = format!("{}_{}_{}", partner_id.0, orcid, Utc::now().timestamp());
        let mut hasher = Sha3_256::new();
        hasher.update(input.as_bytes());
        let session_id = SessionId(hex::encode(&hasher.finalize()[..8]));

        let phi_c_base = PhiC::new(0.88)?;

        Ok(AuthResult {
            partner_id: partner_id.clone(),
            session_id,
            phi_c_base,
            humility,
            authenticated_at: Utc::now(),
        })
    }
}

/// Composite authenticator checking all three invariants
pub struct CompositeAuthenticator {
    ghost: GhostAuthenticator,
}

impl CompositeAuthenticator {
    pub fn new() -> Self {
        Self { ghost: GhostAuthenticator }
    }
}

#[async_trait]
impl Authenticator for CompositeAuthenticator {
    async fn authenticate(
        &self,
        partner_id: &PartnerId,
        orcid: &str,
        humility: HumilityScore,
    ) -> Result<AuthResult, ArkheError> {
        let result = self.ghost.authenticate(partner_id, orcid, humility).await?;

        if result.phi_c_base.0 < LOOPSEAL {
            return Err(ArkheError::BelowGhost(result.phi_c_base.0));
        }

        if result.phi_c_base.0 > GAP_SOVEREIGN {
            return Err(ArkheError::AboveGap(result.phi_c_base.0));
        }

        Ok(result)
    }
}
