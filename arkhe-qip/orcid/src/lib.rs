// ============================================================================
// ARKHE Ω-TEMP v5.7.0 — ORCID Integration Module
// ============================================================================
//
// Este módulo provê integração com o sistema ORCID (Open Researcher and
// Contributor ID), permitindo que pesquisadores ancoram sua identidade
// acadêmica na cadeia temporal ARKHE.
//
// Funcionalidades:
//   1. Autenticação OAuth2/OIDC com ORCID API
//   2. Registro de vínculo ORCID ↔ DataFingerprint
//   3. Prova ZK de posse de ORCID (sem revelar o ID)
//   4. Ponte ORCID → Wallet Pix (via x402 bridge)
//   5. Cálculo de reputação baseada em publicações e datasets
//
// ============================================================================

pub mod auth;
pub mod registry;
pub mod proof;
pub mod bridge;
pub mod reputation;

pub use auth::OrcidAuth;
pub use registry::OrcidRegistry;
pub use proof::OrcidZkProof;
pub use bridge::OrcidPixBridge;

pub use auth::{OrcidRecord, OrcidToken, OrcidAuthError};
pub use registry::{OrcidDataLink, RegistryError};
pub use proof::{ZkProofParams, ProofError};
pub use bridge::WalletAddress;
pub use reputation::{ReputationScore, ReputationSource};
