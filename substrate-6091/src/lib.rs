// ============================================================================
// ARKHE Ω‑TEMP v6.1.0 — Substrato 6091: Multiversal Compliance Engine
// ============================================================================

#![allow(clippy::too_many_arguments)]

mod compliance_graph;
mod cosmic_compliance;
mod cross_universe_proof;
mod financial_compliance;
mod ip_compliance;
mod multiversal_orchestrator;
mod mutual_recognition;
mod quantum_compliance;
mod temporal_compliance;

// ============================================================================
// RE‑EXPORTS
// ============================================================================

pub use compliance_graph::{
    ComplianceEdge, ComplianceGraph, Jurisdiction, JurisdictionVerifier, RegulatoryNode,
    RequirementType,
};

pub use mutual_recognition::{MRABridge, MutualRecognitionAgreement, RecognitionProof};

pub use temporal_compliance::{
    CausalityProof, CausalityViolation, TemporalBlockValidator, TemporalCompliance,
};

pub use quantum_compliance::{
    QuantumCircuitExportProof, QuantumExportConfig, QuantumExportControl, QuantumExportViolation,
    WassenaarChecker,
};

pub use financial_compliance::{
    CrossBorderCompliance, FedNowToPix, FinancialMultiversalBridge, FinancialMultiversalConfig,
    PixToSepa, PixTransaction,
};

pub use ip_compliance::{
    ArtFingerprint, BerneConventionAdapter, IPMultiversalConfig, IPMultiversalProof,
    OrcidToCopyright,
};

pub use cosmic_compliance::{
    ConstantValidator, CosmicConfig, CosmicParameters, CosmicViolation, PhysicalLawCompliance,
    VacuumPermit,
};

pub use cross_universe_proof::{CrossUniverseVerifier, MultiversalProof, UniverseSet};

pub use multiversal_orchestrator::{Artifact, MultiversalCompliance, MultiversalComplianceError};
