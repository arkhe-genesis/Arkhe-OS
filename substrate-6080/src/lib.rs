// ============================================================================
// ARKHE Ω-TEMP v6.1.0 — Substrato 6080: zkLib (Zero-Knowledge Cryptography Library)
// ============================================================================
//
// ═══════════════════════════════════════════════════════════════════════════
//  FUNDAÇÃO CRIPTOGRÁFICA DA CATEDRAL
// ═══════════════════════════════════════════════════════════════════════════
//
// zkLib é a biblioteca canônica de provas de conhecimento zero do ecossistema
// ARKHE. Ela provê todas as primitivas necessárias para os substratos
// superiores (Q-Art, QIP, Cosmology, etc.) gerarem e verificarem provas
// sem revelar dados sensíveis.
//
// Módulos:
//   - circuits:      Definição de circuitos Plonky2 reutilizáveis.
//   - proofs:        Serialização, agregação e cache de provas.
//   - hash:          Poseidon, Rescue-Prime, MiMC para SNARK-friendly hashing.
//   - merkle:        Merkle trees otimizadas para ZK (Poseidon-based).
//   - commitments:   Pedersen, polynomial commitments (KZG, FRI).
//   - groth16:       Interface para Groth16 (via arkworks-rs).
//   - plonky2:       Interface de alto nível para Plonky2.
//   - verifier:      Verificação universal de provas (on-chain e off-chain).
//   - temporal_anchor: Registro de provas na TemporalHashChain.
//
// Features:
//   - plonky2:        Inclui suporte a Plonky2 (padrão).
//   - groth16:        Inclui suporte a Groth16 (arkworks).
//   - full:           Todos os esquemas.
//   - wasm:           Compila para WebAssembly (sem Plonky2).
//
// Exemplo:
//   use {
//       PoseidonHasher, MerkleTree, ZKProof, Plonky2Prover,
//       generate_proof, verify_proof, anchor_to_temporal_chain,
//   };
//
//   let tree = MerkleTree::<PoseidonHasher>::new(&leaves);
//   let root = tree.root();
//   let proof = tree.proof(3).unwrap();
//
// ============================================================================

#![cfg_attr(docsrs, feature(doc_auto_cfg))]

// ============================================================================
// MÓDULOS
// ============================================================================

pub mod circuits;
pub mod commitments;
pub mod hash;
pub mod merkle;
pub mod proofs;
pub mod prover;
pub mod temporal_anchor;
pub mod verifier;

// ============================================================================
// RE-EXPORTS
// ============================================================================

pub use hash::{HashError, HashOutput, MiMCHasher, PoseidonHasher, RescuePrimeHasher};

pub use merkle::{LeafIndex, MerkleError, MerkleProof, MerkleTree, TreeConfig};

pub use commitments::{
    CommitmentError, CommitmentProof, FRICommitment, KZGCommitment, PedersenCommitment,
};

pub use circuits::{
    ArithmeticCircuit, CircuitBuilder, CircuitConfig, CircuitError, Plonky2Circuit,
};

pub use proofs::{
    ProofAggregator, ProofCache, ProofHeader, ProofSerializer, ProofType, ProofWithMetadata,
    ZKProof,
};

pub use prover::{Groth16Prover, Plonky2Prover, ProverTrait, ProvingKey, VerifyingKey};

pub use verifier::{
    BatchVerifier, ProofVerifier, UniversalVerifier, VerificationError, VerificationResult,
};

pub use temporal_anchor::{
    anchor_to_temporal_chain, AnchorProof, AnchoredProof, TemporalProofEvent,
};

#[cfg(test)]
mod tests {
    use super::*;
    use hash::PoseidonHasher;
    use merkle::{MerkleTree, TreeConfig};

    #[test]
    fn test_merkle_proof() {
        let leaves: Vec<Vec<u8>> = (0..8).map(|i: u32| i.to_be_bytes().to_vec()).collect();
        let tree = MerkleTree::<PoseidonHasher>::new(&leaves, &TreeConfig::default())
            .expect("Failed to build tree");

        let root = tree.root();
        assert_eq!(root.len(), 32);

        let proof = tree.proof(LeafIndex(3)).unwrap();
        assert!(proof.verify(&root, &leaves[3]).unwrap());
    }
}
