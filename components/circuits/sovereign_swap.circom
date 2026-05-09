pragma circom 2.1.0;

include "circomlib/bitify.circom";

// circuits/sovereign_swap.circom
// ZK Proof that an AMM trade maintains the product constant K
// without revealing the specific reserves or trade direction.

template SovereignSwapProof() {
    // PRIVATE INPUTS
    signal input private_x_in;        // Initial reserve X
    signal input private_y_in;        // Initial reserve Y
    signal input private_x_out;       // Final reserve X
    signal input private_y_out;       // Final reserve Y
    signal input private_amount_in;   // Input amount

    // PUBLIC INPUTS
    signal input public_pool_id_commitment;
    signal input public_consent_id_commitment;

    // CONSTRAINTS
    // 0. Range checks to prevent field overflow/wrap-around
    component x_in_bits = Num2Bits(64);
    x_in_bits.in <== private_x_in;

    component y_in_bits = Num2Bits(64);
    y_in_bits.in <== private_y_in;

    component x_out_bits = Num2Bits(64);
    x_out_bits.in <== private_x_out;

    component y_out_bits = Num2Bits(64);
    y_out_bits.in <== private_y_out;

    // 1. K-Invariant: X * Y = K must hold (ignoring fees for simplicity)
    signal k_before;
    k_before <== private_x_in * private_y_in;

    signal k_after;
    k_after <== private_x_out * private_y_out;

    // In a real implementation, we handle fees: (x*y) <= (x_new * y_new)
    k_before === k_after;

    // 2. Amount In sanity check
    component amount_bits = Num2Bits(64);
    amount_bits.in <== private_amount_in;

    // 3. Direction Check (Simplified)
    // Proof that private_x_out = private_x_in + private_amount_in
    // or private_y_out = private_y_in + private_amount_in
    signal diff_x;
    diff_x <== private_x_out - private_x_in;

    signal diff_y;
    diff_y <== private_y_out - private_y_in;

    // One of them must match private_amount_in
    (diff_x - private_amount_in) * (diff_y - private_amount_in) === 0;
}

component main = SovereignSwapProof();
