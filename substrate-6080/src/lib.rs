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

pub mod hash;
pub mod merkle;
pub mod commitments;
pub mod circuits;
pub mod proofs;
pub mod prover;
pub mod verifier;
pub mod temporal_anchor;

// ============================================================================
// RE-EXPORTS
// ============================================================================

pub use hash::{
    PoseidonHasher, RescuePrimeHasher, MiMCHasher,
    HashError, HashOutput,
};

pub use merkle::{
    MerkleTree, MerkleProof, MerkleError,
    TreeConfig, LeafIndex,
};

pub use commitments::{
    PedersenCommitment, KZGCommitment, FRICommitment,
    CommitmentProof, CommitmentError,
};

pub use circuits::{
    CircuitBuilder, CircuitConfig, CircuitError,
    ArithmeticCircuit, Plonky2Circuit,
};

pub use proofs::{
    ZKProof, ProofType, ProofHeader, ProofWithMetadata,
    ProofSerializer, ProofAggregator, ProofCache,
};

pub use prover::{
    Plonky2Prover, Groth16Prover, ProverTrait,
    ProvingKey, VerifyingKey,
};

pub use verifier::{
    ProofVerifier, VerificationResult, VerificationError,
    BatchVerifier, UniversalVerifier,
};

pub use temporal_anchor::{
    AnchorProof, AnchoredProof, TemporalProofEvent,
    anchor_to_temporal_chain,
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
