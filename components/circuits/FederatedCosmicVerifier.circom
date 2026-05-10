pragma circom 2.0.0;

include "circomlib/poseidon.circom";
include "circomlib/comparators.circom";

/**
 * FederatedCosmicVerifier: Agrega provas ZK de múltiplos surveys cosmológicos
 */
template FederatedCosmicVerifier(NUM_SURVEYS, TREE_DEPTH) {
    // === Inputs Privados ===
    signal input param_values[NUM_SURVEYS];
    signal input consensus_weights[NUM_SURVEYS];
    signal input source_private_keys[NUM_SURVEYS];
    signal input merkle_paths[NUM_SURVEYS][TREE_DEPTH];
    signal input merkle_siblings[NUM_SURVEYS][TREE_DEPTH];
    signal input nullifiers[NUM_SURVEYS];

    // === Inputs Públicos ===
    signal input merkle_root_public;
    signal input p_min_threshold_public;
    signal input expected_num_valid_proofs;
    signal input tension_detection_threshold;

    // === Outputs ===
    signal output consensus_valid;
    signal output final_value_commitment;
    signal output tension_detected;
    signal output num_valid_proofs;

    signal valid_proofs[NUM_SURVEYS];

    for (var i = 0; i < NUM_SURVEYS; i++) {
        component source_hasher = Poseidon(1);
        source_hasher.inputs[0] <== source_private_keys[i];

        component merkle_checker = MerkleChecker(TREE_DEPTH);
        merkle_checker.leaf <== source_hasher.out;
        for (var j = 0; j < TREE_DEPTH; j++) {
            merkle_checker.siblings[j] <== merkle_siblings[i][j];
            merkle_checker.path[j] <== merkle_paths[i][j];
        }

        component root_validator = IsEqual();
        root_validator.in[0] <== merkle_checker.root;
        root_validator.in[1] <== merkle_root_public;

        component threshold_comparator = GreaterThan(252);
        threshold_comparator.in[0] <== param_values[i];
        threshold_comparator.in[1] <== p_min_threshold_public;

        valid_proofs[i] <== root_validator.out * threshold_comparator.out;
    }

    signal sum_valid[NUM_SURVEYS + 1];
    sum_valid[0] <== 0;
    for (var i = 0; i < NUM_SURVEYS; i++) {
        sum_valid[i+1] <== sum_valid[i] + valid_proofs[i];
    }
    num_valid_proofs <== sum_valid[NUM_SURVEYS];

    component num_validator = IsEqual();
    num_validator.in[0] <== num_valid_proofs;
    num_validator.in[1] <== expected_num_valid_proofs;

    signal weighted_sum_arr[NUM_SURVEYS + 1];
    weighted_sum_arr[0] <== 0;
    for (var i = 0; i < NUM_SURVEYS; i++) {
        weighted_sum_arr[i+1] <== weighted_sum_arr[i] + param_values[i] * consensus_weights[i];
    }
    signal weighted_sum <== weighted_sum_arr[NUM_SURVEYS];

    signal weight_sum_arr[NUM_SURVEYS + 1];
    weight_sum_arr[0] <== 0;
    for (var i = 0; i < NUM_SURVEYS; i++) {
        weight_sum_arr[i+1] <== weight_sum_arr[i] + consensus_weights[i];
    }
    signal weight_sum <== weight_sum_arr[NUM_SURVEYS];

    // Média Ponderada com restrição rigorosa
    signal weighted_average;
    weighted_average <-- (weight_sum != 0) ? weighted_sum / weight_sum : 0;
    signal remainder;
    remainder <-- (weight_sum != 0) ? weighted_sum % weight_sum : 0;

    weighted_sum === weighted_average * weight_sum + remainder;

    component rem_check = LessThan(252);
    rem_check.in[0] <== remainder;
    // Se weight_sum for 0, rem_check.in[1] será 0, e rem_check.out será 0.
    // Mas se weight_sum > 0, queremos remainder < weight_sum.
    rem_check.in[1] <== weight_sum + (1 - IsZero()(weight_sum));

    // Se weight_sum > 0, então rem_check.out deve ser 1.
    // (1 - IsZero()(weight_sum)) * (1 - rem_check.out) === 0
    signal is_positive_weight <== 1 - IsZero()(weight_sum);
    is_positive_weight * (1 - rem_check.out) === 0;

    signal outlier_detected_arr[NUM_SURVEYS + 1];
    outlier_detected_arr[0] <== 0;
    for (var i = 0; i < NUM_SURVEYS; i++) {
        signal diff <== param_values[i] - weighted_average;
        component is_neg = LessThan(252);
        is_neg.in[0] <== diff;
        is_neg.in[1] <== 0;
        signal abs_diff <== (1 - 2*is_neg.out) * diff;

        component tension_comp = GreaterThan(252);
        tension_comp.in[0] <== abs_diff;
        tension_comp.in[1] <== tension_detection_threshold;

        outlier_detected_arr[i+1] <== outlier_detected_arr[i] + tension_comp.out - outlier_detected_arr[i] * tension_comp.out;
    }
    tension_detected <== outlier_detected_arr[NUM_SURVEYS];

    component final_commitment_gen = Poseidon(3);
    final_commitment_gen.inputs[0] <== weighted_average;
    final_commitment_gen.inputs[1] <== num_valid_proofs;
    final_commitment_gen.inputs[2] <== tension_detected;
    final_value_commitment <== final_commitment_gen.out;

    component min_valid_ratio = GreaterThan(252);
    min_valid_ratio.in[0] <== num_valid_proofs * 10;
    min_valid_ratio.in[1] <== expected_num_valid_proofs * 7;

    consensus_valid <== num_validator.out * min_valid_ratio.out;
}

template MerkleChecker(DEPTH) {
    signal input leaf;
    signal input path[DEPTH];
    signal input siblings[DEPTH];
    signal output root;

    signal nodes[DEPTH + 1];
    nodes[0] <== leaf;

    for (var i = 0; i < DEPTH; i++) {
        component hasher = Poseidon(2);
        signal left <== nodes[i] - path[i] * (nodes[i] - siblings[i]);
        signal right <== siblings[i] - path[i] * (siblings[i] - nodes[i]);
        hasher.inputs[0] <== left;
        hasher.inputs[1] <== right;
        nodes[i+1] <== hasher.out;
    }
    root <== nodes[DEPTH];
}

template IsEqual() {
    signal input in[2];
    signal output out;
    signal inv;
    signal diff <== in[0] - in[1];
    inv <-- diff != 0 ? 1/diff : 0;
    out <== -diff*inv + 1;
    diff*out === 0;
}

template IsZero() {
    signal input in;
    signal output out;
    signal inv;
    inv <-- in!=0 ? 1/in : 0;
    out <== -in*inv + 1;
    in*out === 0;
}

component main {public [merkle_root_public, p_min_threshold_public, expected_num_valid_proofs, tension_detection_threshold]} = FederatedCosmicVerifier(6, 20);
