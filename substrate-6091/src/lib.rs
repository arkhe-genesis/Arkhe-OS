// ============================================================================
// ARKHE Ω‑TEMP v6.1.0 — Substrato 6091: Multiversal Compliance Engine
// ============================================================================

#![allow(clippy::too_many_arguments)]

mod compliance_graph;
mod mutual_recognition;
mod temporal_compliance;
mod quantum_compliance;
mod financial_compliance;
mod ip_compliance;
mod cosmic_compliance;
mod cross_universe_proof;
mod multiversal_orchestrator;

// ============================================================================
// RE‑EXPORTS
// ============================================================================

pub use compliance_graph::{
    ComplianceGraph, RegulatoryNode, ComplianceEdge,
    Jurisdiction, RequirementType, JurisdictionVerifier
};

pub use mutual_recognition::{
    MutualRecognitionAgreement, MRABridge,
    RecognitionProof,
};

pub use temporal_compliance::{
    TemporalCompliance, CausalityProof,
    TemporalBlockValidator, CausalityViolation
};

pub use quantum_compliance::{
    QuantumExportControl, WassenaarChecker,
    QuantumCircuitExportProof, QuantumExportConfig, QuantumExportViolation
};

pub use financial_compliance::{
    FinancialMultiversalBridge, PixToSepa, FedNowToPix,
    CrossBorderCompliance, FinancialMultiversalConfig, PixTransaction
};

pub use ip_compliance::{
    BerneConventionAdapter, OrcidToCopyright,
    IPMultiversalProof, IPMultiversalConfig, ArtFingerprint
};

pub use cosmic_compliance::{
    PhysicalLawCompliance, ConstantValidator,
    VacuumPermit, CosmicConfig, CosmicParameters, CosmicViolation
};

pub use cross_universe_proof::{
    MultiversalProof, UniverseSet,
    CrossUniverseVerifier,
};

pub use multiversal_orchestrator::{MultiversalCompliance, Artifact, MultiversalComplianceError};
