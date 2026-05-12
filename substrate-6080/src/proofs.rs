#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct ZKProof;

impl ZKProof {
    pub fn aggregate(_proofs: &[ZKProof]) -> Result<Self, crate::verifier::VerificationError> {
        Ok(Self)
    }
}

pub struct ProofType;
pub struct ProofHeader;
pub struct ProofWithMetadata;
pub struct ProofSerializer;
pub struct ProofAggregator;
pub struct ProofCache;
