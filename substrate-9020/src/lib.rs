// ============================================================================
// ARKHE Ω‑TEMP v6.1.0 — Substrato 9020: Daybreak‑ARKHE Security Synthesis
// ============================================================================
//
// ═══════════════════════════════════════════════════════════════════════════
//  IMMUNE SYSTEM OF THE MULTIVERSE
// ═══════════════════════════════════════════════════════════════════════════
//
// This substrate bridges OpenAI's Daybreak defensive architecture with
// ARKHE's self‑verifying multiversal fabric. It implements agentic patch
// verification, threat modeling as a compliance graph, ZK‑proven
// non‑regression, trust tiers via ORCID/KYC, and immutable audit trails.
//
// Example:
//   use arkhe_daybreak::{
//       SecurityAgent, ThreatModel, PatchProof, TrustTier,
//       CodeReviewHarness, DependencyAudit,
//   };
//
//   let agent = SecurityAgent::new(AgentConfig::daybreak());
//   let threat = ThreatModel::from_compliance_graph(&compliance);
//   let proof = agent.verify_patch(&patch, &threat).await?;
//   agent.anchor_audit(&proof).await?;
// ============================================================================

#![allow(clippy::too_many_arguments)]

mod agent;
mod audit;
mod code_review;
mod dependency_audit;
mod integration;
mod patch_verification;
mod threat_model;
mod trust_tiers;

pub use agent::{SecurityAgent, SecurityAgentConfig};
pub use audit::DaybreakAudit;
pub use code_review::{CodeReviewHarness, ReviewResult};
pub use dependency_audit::{DependencyAudit, DependencyRisk};
pub use patch_verification::{PatchProof, PatchValidator};
pub use threat_model::{AttackVector, ThreatModel, ThreatNode};
pub use trust_tiers::{TieredAccessControl, TrustTier};
