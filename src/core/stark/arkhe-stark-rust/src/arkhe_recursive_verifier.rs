// arkhe_recursive_verifier.rs — Circuito de verificação recursiva

use winterfell::{
    verify, StarkProof, VerifierError,
    math::fields::f128::BaseElement,
};
use sha2::{Sha256, Digest};
use crate::arkhe_merkabah_air::{MerkabahAir, MerkabahInputs};
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VerifiedProof {
    pub merkle_root: [u8; 32],
    pub aggregated_coherence: [u8; 16],
    pub aggregated_phase: [u8; 16],
    pub num_leaf_proofs: u32,
    pub level: u8,
}

pub struct RecursiveJoinCircuit;

impl RecursiveJoinCircuit {
    pub fn join(
        left: &StarkProof,
        right: &StarkProof,
        left_inputs: &MerkabahInputs,
        right_inputs: &MerkabahInputs,
    ) -> Result<VerifiedProof, VerifierError> {
        let _left_valid = verify::<MerkabahAir, winterfell::crypto::hashers::Blake3_256<BaseElement>, winterfell::crypto::DefaultRandomCoin<winterfell::crypto::hashers::Blake3_256<BaseElement>>>(left.clone(), left_inputs.clone(), &winterfell::AcceptableOptions::OptionSet(vec![]))?;

        let _right_valid = verify::<MerkabahAir, winterfell::crypto::hashers::Blake3_256<BaseElement>, winterfell::crypto::DefaultRandomCoin<winterfell::crypto::hashers::Blake3_256<BaseElement>>>(right.clone(), right_inputs.clone(), &winterfell::AcceptableOptions::OptionSet(vec![]))?;

        let _agg_coherence = (left_inputs.final_coherence + right_inputs.final_coherence)
            / BaseElement::new(2);

        let _agg_phase = left_inputs.final_phase;

        let mut hasher = Sha256::new();
        hasher.update(&left.to_bytes());
        hasher.update(&right.to_bytes());
        let merkle_root: [u8; 32] = hasher.finalize().into();

        let agg_coherence_bytes = [0u8; 16];

        Ok(VerifiedProof {
            merkle_root,
            aggregated_coherence: agg_coherence_bytes,
            aggregated_phase: agg_coherence_bytes,
            num_leaf_proofs: 2,
            level: 1,
        })
    }

    pub fn aggregate_tree(
        proofs: &[StarkProof],
        inputs: &[MerkabahInputs],
    ) -> Result<VerifiedProof, VerifierError> {
        if proofs.len() != inputs.len() {
            return Err(VerifierError::ProofDeserializationError("Length mismatch".to_string()));
        }
        assert!(proofs.len().is_power_of_two(), "N deve ser potência de 2");

        let mut current: Vec<(StarkProof, MerkabahInputs)> =
            proofs.iter().cloned().zip(inputs.iter().cloned()).collect();

        let mut level: u8 = 0;
        while current.len() > 1 {
            let mut next = Vec::new();
            for i in (0..current.len()).step_by(2) {
                let (left_p, left_i) = &current[i];
                let (right_p, right_i) = &current[i + 1];

                let joined = Self::join(left_p, right_p, left_i, right_i)?;

                next.push((proofs[0].clone(), MerkabahInputs::from_joined(&joined)));
            }
            current = next;
            level += 1;
        }

        let agg_coherence_bytes = [0u8; 16];

        Ok(VerifiedProof {
            merkle_root: current[0].0.to_bytes()[0..32].try_into().unwrap_or([0; 32]),
            aggregated_coherence: agg_coherence_bytes,
            aggregated_phase: agg_coherence_bytes,
            num_leaf_proofs: proofs.len() as u32,
            level,
        })
    }
}
