pragma circom 2.1.0;

include "circomlib/comparators.circom";
include "circomlib/bitify.circom";
include "circomlib/poseidon.circom";

template HumanCoherenceProof() {
    // Inputs (Scaled by 1e9)
    signal input omega_behavior;
    signal input entropy_timing;
    signal input fractal_dim;
    signal input nonce;

    // Public Inputs
    signal input min_omega;
    signal input max_omega;
    signal input min_entropy;
    signal input max_fractal;

    // Output
    signal output commitment;

    // 0. Range checks to prevent field wrap-around exploits
    component omega_bits = Num2Bits(64);
    omega_bits.in <== omega_behavior;

    component entropy_bits = Num2Bits(64);
    entropy_bits.in <== entropy_timing;

    component fractal_bits = Num2Bits(64);
    fractal_bits.in <== fractal_dim;

    component min_omega_bits = Num2Bits(64);
    min_omega_bits.in <== min_omega;

    component max_omega_bits = Num2Bits(64);
    max_omega_bits.in <== max_omega;

    component min_entropy_bits = Num2Bits(64);
    min_entropy_bits.in <== min_entropy;

    component max_fractal_bits = Num2Bits(64);
    max_fractal_bits.in <== max_fractal;

    // 1. Check Omega range [min, max]
    component check_omega_min = LessThan(64);
    check_omega_min.in[0] <== min_omega;
    check_omega_min.in[1] <== omega_behavior;
    check_omega_min.out === 1;

    component check_omega_max = LessThan(64);
    check_omega_max.in[0] <== omega_behavior;
    check_omega_max.in[1] <== max_omega;
    check_omega_max.out === 1;

    // 2. Check Entropy (min)
    component check_entropy = LessThan(64);
    check_entropy.in[0] <== min_entropy;
    check_entropy.in[1] <== entropy_timing;
    check_entropy.out === 1;

    // 3. Check Fractal Dimension (max)
    component check_fractal = LessThan(64);
    check_fractal.in[0] <== fractal_dim;
    check_fractal.in[1] <== max_fractal;
    check_fractal.out === 1;

    // 4. Generate Commitment
    component hasher = Poseidon(4);
    hasher.inputs[0] <== omega_behavior;
    hasher.inputs[1] <== entropy_timing;
    hasher.inputs[2] <== fractal_dim;
    hasher.inputs[3] <== nonce;

    commitment <== hasher.out;
}

component main {public [min_omega, max_omega, min_entropy, max_fractal]} = HumanCoherenceProof();
