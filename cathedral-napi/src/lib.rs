//! cathedral-napi – Native Node.js binding for Cathedral ARKHE
//!
//! Exposes:
//! - `prove_memory_state()` – generates a DLA memory proof
//! - `CathedralAgent` – wrapper around EmbodiedCognitiveCore for full agent control

#![deny(clippy::all)]

use napi::bindgen_prelude::*;
use napi_derive::napi;
use tokio::sync::Mutex;
use std::sync::Arc;

// ════════════════════════════════════════════════════════════════
// 1. DLA Memory Proof (standalone function)
// ════════════════════════════════════════════════════════════════

#[derive(serde::Serialize, serde::Deserialize)]
#[napi(object)]
pub struct MemoryProof {
    pub merkle_root: String,
    pub timestamp: u64,
    pub state_count: u32,
}

/// Generate a cryptographic commitment to the current DLA memory state.
/// This can be called from TypeScript without instantiating the full agent.
#[napi]
pub async fn prove_memory_state() -> Result<MemoryProof> {
    // In production, replace with actual DLA call (FFI, HTTP, or direct engine)
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs();

    // Mock merkle root (use blake3 or real DLA)
    let merkle_root = format!(
        "0x{:064x}",
        blake3::hash(format!("dla_memory_{}", timestamp).as_bytes()).as_bytes()[..8]
            .iter()
            .fold(0u64, |acc, &b| (acc << 8) | b as u64)
    );

    Ok(MemoryProof {
        merkle_root,
        timestamp,
        state_count: 47, // example
    })
}

// ════════════════════════════════════════════════════════════════
// 2. CathedralAgent – High‑level wrapper for EmbodiedCognitiveCore
// ════════════════════════════════════════════════════════════════

// We assume cathedral-embodied-no_std is a dependency of this crate
use cathedral_embodied_no_std::core::embodied_cognitive_core::EmbodiedCognitiveCore;

#[napi]
pub struct CathedralAgent {
    core: Arc<Mutex<EmbodiedCognitiveCore>>,
}

#[napi]
impl CathedralAgent {
    /// Creates a new agent instance.
    /// Reads environment variables:
    /// - PICOADS_API_KEY
    /// - PICOADS_BACKEND_URL
    /// - SUCCESS_RECORDER_DB (optional, for SQLite persistence)
    #[napi(constructor)]
    pub fn new() -> napi::Result<Self> {
        let picoads_api_key = std::env::var("PICOADS_API_KEY").ok();
        let picoads_backend = std::env::var("PICOADS_BACKEND_URL").ok();
        let recorder_db = std::env::var("SUCCESS_RECORDER_DB").ok();

        let core = EmbodiedCognitiveCore::new(picoads_api_key, picoads_backend, recorder_db.as_deref());

        Ok(Self {
            core: Arc::new(Mutex::new(core)),
        })
    }

    /// Execute a single cognitive tick (async from Node.js)
    #[napi]
    pub async fn tick(&self) -> napi::Result<String> {
        let mut core = self.core.lock().await;
        core.tick_zk_with_accelerator().await.map_err(|e| napi::Error::from_reason(e.to_string()))?;
        Ok("tick_complete".to_string())
    }

    /// Retrieve the current policy as a JSON string
    #[napi]
    pub async fn get_policy(&self) -> napi::Result<String> {
        let core = self.core.lock().await;
        serde_json::to_string(&core.current_policy)
            .map_err(|e| napi::Error::from_reason(e.to_string()))
    }

    /// Record that a recommendation was accepted by the user
    #[napi]
    pub async fn accept_recommendation(&self, rec_id: String) -> napi::Result<()> {
        let mut core = self.core.lock().await;
        core.accept_recommendation(&rec_id);
        Ok(())
    }

    /// Get current round number
    #[napi]
    pub async fn current_round(&self) -> napi::Result<u32> {
        let core = self.core.lock().await;
        Ok(core.current_round)
    }

    /// Fetch PicoAds recommendations directly from the core (returns JSON array)
    #[napi]
    pub async fn get_recommendations(
        &self,
        query: String,
        hub: Option<String>,
        max_results: Option<u32>,
    ) -> napi::Result<String> {
        let core = self.core.lock().await;
        let recs = core
            .get_picoads_recommendations(&query, hub.as_deref(), max_results)
            .await
            .map_err(|e| napi::Error::from_reason(e.to_string()))?;

        serde_json::to_string(&recs).map_err(|e| napi::Error::from_reason(e.to_string()))
    }
}

// Required by napi-rs
#[napi]
pub fn init() {}
