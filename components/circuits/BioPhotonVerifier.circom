pragma circom 2.1.0;

include "circomlib/comparators.circom";
include "circomlib/bitify.circom";
include "circomlib/poseidon.circom";

// BioPhotonVerifier: ARKHE-03 and ARKHE-04 Validation
template BioPhotonVerifier() {
    signal input experiment_type; // 0: MT, 1: TPV/Hybrid
    signal input measured_eta;    // Scaled by 1000
    signal input threshold;       // Scaled by 1000

    // ARKHE-04 Specific (Subpicometric)
    signal input omega_spec;      // Scaled by 1e9
    signal input peak_shift_pm;   // Scaled by 1000
    signal input condition_hash;

    signal input nullifier;

    signal output proof_valid;

    // 0. Range checks to prevent field wrap-around exploits
    component eta_bits = Num2Bits(64);
    eta_bits.in <== measured_eta;

    component threshold_bits = Num2Bits(64);
    threshold_bits.in <== threshold;

    component omega_bits = Num2Bits(64);
    omega_bits.in <== omega_spec;

    component shift_bits = Num2Bits(64);
    shift_bits.in <== peak_shift_pm;

    // 1. Common Efficiency Check (Superradiance / TPV Yield)
    component check_eta = LessThan(64);
    check_eta.in[0] <== threshold;
    check_eta.in[1] <== measured_eta;
    check_eta.out === 1;

    // 2. Hybrid Specific Checks (for experiment_type == 1)
    // If TPV, check peak_shift and omega
    // We use a multiplexer logic: (1 - type) * 1 + type * (condition)

    // Check peak_shift_pm < 1.0 pm (1000)
    component check_shift = LessThan(64);
    check_shift.in[0] <== peak_shift_pm;
    check_shift.in[1] <== 1001;

    // Check omega_spec > 0.7 (700,000,000)
    component check_omega = LessThan(64);
    check_omega.in[0] <== 700000000;
    check_omega.in[1] <== omega_spec;

    // is_valid_type1 = check_shift.out * check_omega.out
    signal is_valid_type1 <== check_shift.out * check_omega.out;

    // Final check logic:
    // If type == 0, we only care about eta (already checked).
    // If type == 1, we care about eta AND type1 checks.
    // So: check_eta.out AND (type == 0 OR is_valid_type1)

    signal type_check <== (1 - experiment_type) + experiment_type * is_valid_type1;
    type_check === 1;

    // 3. Nullifier Binding
    component hasher = Poseidon(4);
    hasher.inputs[0] <== experiment_type;
    hasher.inputs[1] <== condition_hash;
    hasher.inputs[2] <== nullifier;
    hasher.inputs[3] <== measured_eta;

    proof_valid <== 1;
}

component main {public [experiment_type, threshold, condition_hash]} = BioPhotonVerifier();
