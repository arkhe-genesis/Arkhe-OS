//! Arkhe Fractal Wave Engine Module
//!
//! Roundless consensus over HyperCycle and distributed FFT.


use crate::{PhiC, ArkheError};

/// Represents a simple state wavelet for the roundless consensus.
#[derive(Debug, Clone)]
pub struct StateWavelet {
    pub validator_id: String,
    pub state_hash: String,
    pub phi_c: PhiC,
    pub timestamp_ms: u64,
    pub amplitude: f64,
    pub phase: f64,
}

/// The local view of a roundless validator
pub struct RoundlessValidator {
    pub id: String,
    pub local_state_hash: Option<String>,
    pub local_phi_c: PhiC,
    history: Vec<StateWavelet>,
}

impl RoundlessValidator {
    pub fn new(id: String, initial_phi_c: f64) -> Result<Self, ArkheError> {
        Ok(Self {
            id,
            local_state_hash: None,
            local_phi_c: PhiC::new(initial_phi_c)?,
            history: Vec::new(),
        })
    }

    /// Emit the local state as a wavelet
    pub fn emit_wavelet(&self, timestamp_ms: u64, phase: f64) -> StateWavelet {
        StateWavelet {
            validator_id: self.id.clone(),
            state_hash: self.local_state_hash.clone().unwrap_or_else(|| "00000000".to_string()),
            phi_c: self.local_phi_c,
            timestamp_ms,
            amplitude: 1.0,
            phase,
        }
    }

    /// Receive a wavelet and store it
    pub fn receive_wavelet(&mut self, wavelet: StateWavelet) {
        self.history.push(wavelet);
    }

    /// Aggregates recent wavelets to determine if a supermajority consensus has been reached.
    pub fn confirm_state(&mut self, current_time_ms: u64, window_ms: u64, total_peers: usize) -> Option<String> {
        let mut counts = std::collections::HashMap::new();

        for w in &self.history {
            if current_time_ms.saturating_sub(w.timestamp_ms) <= window_ms {
                *counts.entry(w.state_hash.clone()).or_insert(0) += 1;
            }
        }

        let threshold = (total_peers as f64 * 0.76).ceil() as usize;

        for (state_hash, count) in counts {
            if count >= threshold {
                self.local_state_hash = Some(state_hash.clone());
                return Some(state_hash);
            }
        }

        None
    }
}
