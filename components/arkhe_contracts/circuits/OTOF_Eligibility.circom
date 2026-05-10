// SPDX-License-Identifier: MIT
pragma circom 2.0.0;

/**
 * @title OTOFEligibilityProof
 * @notice Circuito ZK para provar elegibilidade genética OTOF sem expor sequência
 * @dev Verifica se hash(genetic_sequence + salt) está na Merkle tree de mutações válidas
 * @author Arkhe-Ω Consortium
 */

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";

/**
 * @template MerkleTreeInclusionProof
 * @notice Implementação manual de prova de inclusão Merkle
 */
template MerkleTreeInclusionProof(nLevels) {
    signal input leaf;
    signal input root;
    signal input pathElements[nLevels];
    signal input pathIndices[nLevels];

    component hashers[nLevels];
    signal levelHashes[nLevels + 1];

    levelHashes[0] <== leaf;

    for (var i = 0; i < nLevels; i++) {
        hashers[i] = Poseidon(2);

        // Se pathIndices[i] == 0, levelHashes[i] é esquerda, pathElements[i] é direita
        // Se pathIndices[i] == 1, pathElements[i] é esquerda, levelHashes[i] é direita
        signal left <== (pathElements[i] - levelHashes[i]) * pathIndices[i] + levelHashes[i];
        signal right <== (levelHashes[i] - pathElements[i]) * pathIndices[i] + pathElements[i];

        hashers[i].inputs[0] <== left;
        hashers[i].inputs[1] <== right;

        levelHashes[i+1] <== hashers[i].out;
    }

    root === levelHashes[nLevels];
}

template OTOFEligibilityProof(nLevels) {
    // Inputs privados (não revelados na prova)
    signal input geneticSequence;      // Sequência genética do paciente (privada)
    signal input salt;                 // Salt aleatório 256-bit (privado)
    signal input mutationIndex;        // Índice da mutação na árvore (privado)
    signal input pathElements[nLevels]; // Elementos do caminho Merkle (privado)
    signal input pathIndices[nLevels];  // Índices (0/1) do caminho Merkle (privado)

    // Inputs públicos (revelados para verificação)
    signal input merkleRoot;           // Raiz da Merkle tree de mutações OTOF (pública)
    signal input nullifierSeed;        // Seed para prevenir double-spending (pública)

    // Output público
    signal output nullifier;           // Hash único para prevenir re-uso
    signal output geneticHash;         // Hash anônimo do paciente (commitment)

    // 1. Calcula hash da sequência genética + salt (Poseidon)
    component hasher = Poseidon(2);
    hasher.inputs[0] <== geneticSequence;
    hasher.inputs[1] <== salt;

    geneticHash <== hasher.out;

    // 2. Verifica se geneticHash está na Merkle tree (inclusão)
    component leafHasher = Poseidon(1);
    leafHasher.inputs[0] <== geneticHash;

    component merkleProof = MerkleTreeInclusionProof(nLevels);
    merkleProof.leaf <== leafHasher.out;
    merkleProof.root <== merkleRoot;
    for (var i = 0; i < nLevels; i++) {
        merkleProof.pathElements[i] <== pathElements[i];
        merkleProof.pathIndices[i] <== pathIndices[i];
    }

    // 3. Gera nullifier único (prevents double-enrollment)
    component nullifierHasher = Poseidon(2);
    nullifierHasher.inputs[0] <== geneticHash;
    nullifierHasher.inputs[1] <== nullifierSeed;

    nullifier <== nullifierHasher.out;

    // 4. Verificações de range (sanity checks)
    // Garante que mutationIndex está dentro dos limites (0 a 2^nLevels)
    component rangeCheck = LessThan(32);
    rangeCheck.in[0] <== mutationIndex;
    rangeCheck.in[1] <== 2 ** nLevels;
    rangeCheck.out === 1;
}

// Instanciação para árvore de 20 níveis (~1 milhão de folhas)
component main = OTOFEligibilityProof(20);
