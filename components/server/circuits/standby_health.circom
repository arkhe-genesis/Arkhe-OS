pragma circom 2.1.6;

include "node_modules/circomlib/circuits/comparators.circom";
include "node_modules/circomlib/circuits/poseidon.circom";

// StandbyHealthProof: Verifica se o nó standby está saudável (T2* > 45000 ns)
// Inputs:
// - private: t2_star (ns)
// - public: node_id, threshold (45000), timestamp
template StandbyHealthProof() {
    signal input t2_star;
    signal input node_id;
    signal input threshold;
    signal input timestamp;

    signal output hash;
    signal output is_healthy;

    // 1. Verifica se T2* > threshold
    component gt = GreaterThan(64); // Suporta até 2^64
    gt.in[0] <== t2_star;
    gt.in[1] <== threshold;

    is_healthy <== gt.out;
    is_healthy === 1; // Força a prova a ser válida apenas se saudável

    // 2. Compromisso (Commitment) do estado do nó
    component hasher = Poseidon(3);
    hasher.inputs[0] <== node_id;
    hasher.inputs[1] <== t2_star;
    hasher.inputs[2] <== timestamp;

    hash <== hasher.out;
}

component main {public [node_id, threshold, timestamp]} = StandbyHealthProof();
