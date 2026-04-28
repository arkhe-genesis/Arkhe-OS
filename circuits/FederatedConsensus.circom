pragma circom 2.0.0;

include "circomlib/poseidon.circom";
include "circomlib/comparators.circom";
include "circomlib/bitify.circom";

/**
 * FederatedConsensus.circom
 * Verifica se provas independentes de múltiplos telescópios são mutuamente consistentes
 */
template FederatedConsensus() {
    signal input p_occ_survey_A;
    signal input p_occ_survey_B;
    signal input methodology_id_A;
    signal input methodology_id_B;
    signal input delta_p_max_allowed;
    signal input commitment_survey_A;
    signal input commitment_survey_B;
    signal input pipeline_hash_A;
    signal input pipeline_hash_B;

    signal output is_federated_consensus;
    signal output combined_data_commitment;

    // 0. Range checks to prevent field wrap-around exploits
    component p_a_bits = Num2Bits(252);
    p_a_bits.in <== p_occ_survey_A;

    component p_b_bits = Num2Bits(252);
    p_b_bits.in <== p_occ_survey_B;

    component delta_bits = Num2Bits(252);
    delta_bits.in <== delta_p_max_allowed;

    component method_check = IsEqual();
    method_check.in[0] <== methodology_id_A;
    method_check.in[1] <== methodology_id_B;
    signal methods_are_distinct <== 1 - method_check.out;

    component commit_gen_A = Poseidon(3);
    commit_gen_A.inputs[0] <== p_occ_survey_A;
    commit_gen_A.inputs[1] <== methodology_id_A;
    commit_gen_A.inputs[2] <== pipeline_hash_A;
    component commit_check_A = IsEqual();
    commit_check_A.in[0] <== commit_gen_A.out;
    commit_check_A.in[1] <== commitment_survey_A;

    component commit_gen_B = Poseidon(3);
    commit_gen_B.inputs[0] <== p_occ_survey_B;
    commit_gen_B.inputs[1] <== methodology_id_B;
    commit_gen_B.inputs[2] <== pipeline_hash_B;
    component commit_check_B = IsEqual();
    commit_check_B.in[0] <== commit_gen_B.out;
    commit_check_B.in[1] <== commitment_survey_B;

    signal diff <== p_occ_survey_A - p_occ_survey_B;
    component is_neg = LessThan(252);
    is_neg.in[0] <== p_occ_survey_A;
    is_neg.in[1] <== p_occ_survey_B;
    signal abs_diff <== is_neg.out * (p_occ_survey_B - p_occ_survey_A) + (1 - is_neg.out) * diff;

    // Ensure abs_diff is also properly constrained
    component abs_diff_bits = Num2Bits(252);
    abs_diff_bits.in <== abs_diff;

    component within_tolerance = LessThan(252);
    within_tolerance.in[0] <== abs_diff;
    within_tolerance.in[1] <== delta_p_max_allowed;

    is_federated_consensus <== methods_are_distinct * commit_check_A.out * commit_check_B.out * within_tolerance.out;

    component root_commit = Poseidon(2);
    root_commit.inputs[0] <== commitment_survey_A;
    root_commit.inputs[1] <== commitment_survey_B;
    combined_data_commitment <== root_commit.out;
}

// 3 public signals: delta_p_max_allowed, commitment_survey_A, commitment_survey_B
component main {public [delta_p_max_allowed, commitment_survey_A, commitment_survey_B]} = FederatedConsensus();
