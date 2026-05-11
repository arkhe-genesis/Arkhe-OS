pub mod coherence_proof;
pub mod regulatory_verifier;

pub mod zk_lib {
    #[derive(Debug, Clone)]
    pub struct ZKProof(pub Vec<u8>);
}

#[derive(Debug)]
pub struct VerificationError(pub String);

impl std::fmt::Display for VerificationError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

pub struct VerificationReport {
    pub message: String,
}

impl std::fmt::Display for VerificationReport {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.message)
    }
}

pub struct RegulatoryConfig {
    pub min_coverage: f64,
}

pub fn load_proof(_path: &str) -> coherence_proof::CoherenceProof {
    coherence_proof::CoherenceProof {
        merkle_root: [0; 32],
        exploration_coverage: 1.0,
        inner_zk: zk_lib::ZKProof(vec![]),
        temporal_anchor: 0,
    }
}
