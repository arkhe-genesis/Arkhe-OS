// circuits/unified_emission_proof_rtd.circom
// Versão com bridge_commitment e correção temporal

pragma circom 2.1.0;
include "circomlib/circuits/comparators.circom";
// include "merkle_tree.circom"; // Assuming it exists in the environment or will be provided

template UnifiedEmissionProofRTD() {
    // Public Inputs (adicionados campos RTD)
    signal input omega_measured_q;
    signal input omega_target_q;
    signal input tolerance_q;
    signal input merkle_root_neural_p1;
    signal input merkle_root_neural_p2;
    signal input bio_z_score_q;

    signal input sic_measured_q;
    signal input sic_target_q;
    signal input rho_measured_q;
    signal input rho_target_q;
    signal input eta_measured_q;
    signal input eta_target_q;
    signal input merkle_root_optical_p1;
    signal input merkle_root_optical_p2;

    // Bridge commitment (hash dos pesos treinados)
    signal input bridge_commitment_p1;
    signal input bridge_commitment_p2;

    // RTD: correção temporal e espacial
    signal input timestamp_tdb_q;  // Timestamp em escala TDB × 1e9
    signal input location_lat_q;   // Latitude × 1e6
    signal input location_lon_q;   // Longitude × 1e6
    signal input sagnac_corr_ns_q; // Correção Sagnac em nanosegundos

    // Private Witness
    signal private neural_seed;
    // signal private neural_signal_samples[256];
    // signal private neural_merkle_path[8][2];

    signal private l_p;  // Carga topológica (1,2,3)
    signal private m;
    signal private ratio;
    // signal private optical_samples[128];
    // signal private optical_merkle_path[7][2];

    signal private bridge_weights_hash;  // Hash interno dos pesos

    // Constraints: Neural + Optical (simplified for logic verification)
    // In a real scenario, full Merkle and physics validation would be here.

    // Constraint: Bridge commitment matches internal hash
    component bridge_commit_check = IsEqual();
    bridge_commit_check.in[0] <== bridge_commitment_p1;
    bridge_commit_check.in[1] <== bridge_weights_hash;

    // Constraint: RTD consistency (simplificada)
    // Verifica que timestamp_tdb está dentro de janela válida
    component time_window = LessEqThan(64);
    time_window.in[0] <== timestamp_tdb_q;
    time_window.in[1] <== 1714329845000000000 + 86400000000000;  // Janela de 24h em TDB

    // Constraint: Localização válida (latitude entre -90 e 90)
    component lat_valid = LessEqThan(32);
    lat_valid.in[0] <== location_lat_q + 90000000;  // +90° em unidades ×1e6
    lat_valid.in[1] <== 180000000;  // 180° em unidades ×1e6

    // Output
    signal output valid;
    valid <== bridge_commit_check.out *
              time_window.out *
              lat_valid.out;
}

component main { public [
    omega_measured_q, omega_target_q, tolerance_q,
    merkle_root_neural_p1, merkle_root_neural_p2,
    bio_z_score_q,
    sic_measured_q, sic_target_q,
    rho_measured_q, rho_target_q,
    eta_measured_q, eta_target_q,
    merkle_root_optical_p1, merkle_root_optical_p2,
    bridge_commitment_p1, bridge_commitment_p2,
    timestamp_tdb_q, location_lat_q, location_lon_q, sagnac_corr_ns_q
]} = UnifiedEmissionProofRTD();
