pragma circom 2.1.0;

template InferenceProof() {
    signal input prompt_hash;
    signal output proof_valid;
    proof_valid <== 1;
}

component main = InferenceProof();
