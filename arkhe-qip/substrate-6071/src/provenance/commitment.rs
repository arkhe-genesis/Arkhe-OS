use blake3;
use sha3::{Sha3_256, Digest};
use rand::RngCore;
use tracing::debug;
use serde::{Serialize, Deserialize};

/// Pedersen commitment
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct PedersenCommitment {
    pub committe: [u8; 32],    // O commitment
    pub opener: [u8; 32],      // O randomizador (usado para abertura)
}

pub struct CommitmentScheme;

impl CommitmentScheme {
    pub fn pedersen_commit(data: &[u8], blinding: &[u8; 32]) -> PedersenCommitment {
        let mut hasher = Sha3_256::new();
        hasher.update(data);
        hasher.update(blinding);
        let commit = hasher.finalize();

        PedersenCommitment {
            committe: commit.into(),
            opener: *blinding,
        }
    }
}
