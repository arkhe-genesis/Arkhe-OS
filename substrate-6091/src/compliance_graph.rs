use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum Jurisdiction {
    HIPAA,
    GDPR,
    ANVISA,
    FDA,
    PIX_BRASIL,
    SEPA_EU,
    BERNE_COPYRIGHT,
    QUANTUM_WASSENAAR,
    COSMIC_LAW,
    Other(String),
}

pub struct ComplianceGraph;

impl ComplianceGraph {
    pub fn new() -> Self {
        Self
    }
}

pub struct RegulatoryNode;
pub struct ComplianceEdge;
pub struct RequirementType;

pub trait JurisdictionVerifier {}
