// arkhe_sync_proof_node.rs — Prova STARK por nó via Risc0 zkVM
// Usa Risc0 (https://github.com/risc0/risc0) para executar código Rust em zkVM

use risc0_zkvm::{guest::env, serde, sha, Receipt};

#[derive(serde::Serialize, serde::Deserialize, Clone)]
pub struct SyncMeasurement {
    pub node_a_time_ns: u64,
    pub node_b_time_ns: u64,
    pub wr_offset_ps: i64,
}

// Estrutura de entrada para a prova
#[derive(serde::Serialize, serde::Deserialize)]
pub struct SyncProofInput {
    pub node_id: String,
    pub measurements: Vec<SyncMeasurement>,  // Dados brutos de sincronização
    pub peer_node_id: String,
    pub fingerprint_freq_hz: f64,
    pub phase_tolerance_rad: f64,
}

// Estrutura de saída (pública, verificável)
#[derive(serde::Serialize, serde::Deserialize, Clone)]
pub struct SyncProofOutput {
    pub node_id_hash: [u8; 32],           // SHA256 do node_id
    pub peer_node_id_hash: [u8; 32],
    pub jitter_rms_ns: f64,
    pub phase_error_rad: f64,
    pub is_coherent: bool,
    pub num_measurements: u32,
    pub timestamp: u64,
}

// Função executada dentro da zkVM (prova que os cálculos foram feitos corretamente)
fn main() {
    // Ler inputs públicos e privados
    let input: SyncProofInput = env::read();

    // Calcular métricas de sincronização (executado dentro do zkVM)
    let jitter_rms = compute_jitter_rms(&input.measurements);
    let phase_error = 2.0 * std::f64::consts::PI * input.fingerprint_freq_hz * jitter_rms * 1e-9;
    let is_coherent = phase_error < input.phase_tolerance_rad;

    // Hash dos node_ids para privacidade
    let node_id_hash = *sha::digest(input.node_id.as_bytes()).as_bytes();
    let peer_hash = *sha::digest(input.peer_node_id.as_bytes()).as_bytes();

    let node_id_hash_array: [u8; 32] = node_id_hash.try_into().unwrap_or([0; 32]);
    let peer_hash_array: [u8; 32] = peer_hash.try_into().unwrap_or([0; 32]);

    // Construir output público
    let output = SyncProofOutput {
        node_id_hash: node_id_hash_array,
        peer_node_id_hash: peer_hash_array,
        jitter_rms_ns: jitter_rms,
        phase_error_rad: phase_error,
        is_coherent,
        num_measurements: input.measurements.len() as u32,
        timestamp: risc0_zkvm::guest::env::get_cycle_count(),
    };

    // Commit ao output e finalizar a prova
    env::commit(&output);
}

// Função auxiliar (executada dentro do zkVM)
fn compute_jitter_rms(measurements: &[SyncMeasurement]) -> f64 {
    if measurements.is_empty() {
        return 0.0;
    }
    let diffs: Vec<f64> = measurements
        .iter()
        .map(|m| m.node_a_time_ns as f64 - m.node_b_time_ns as f64 - m.wr_offset_ps as f64 / 1000.0)
        .collect();
    let mean = diffs.iter().sum::<f64>() / diffs.len() as f64;
    let variance = diffs.iter().map(|d| (d - mean).powi(2)).sum::<f64>() / diffs.len() as f64;
    variance.sqrt()
}
