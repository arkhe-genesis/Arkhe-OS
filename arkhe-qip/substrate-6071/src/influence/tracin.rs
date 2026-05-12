use std::sync::{Arc, Mutex};
use half::f16;
use tracing::debug;

use crate::types::InfluenceResult;

/// Calculador de influência TracIn
pub struct TracInCalculator {
    /// Número de checkpoints a considerar
    num_checkpoints: usize,

    /// Threshold de similaridade cosine
    similarity_threshold: f64,

    /// Cache de gradientes (opcional)
    gradient_cache: Arc<Mutex<Vec<(u64, Vec<f32>)>>>,
}

impl TracInCalculator {
    pub fn new(similarity_threshold: f64) -> Self {
        Self {
            num_checkpoints: 10,
            similarity_threshold,
            gradient_cache: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub fn calculate_influence(
        &self,
        data_gradient: &[f32],
        shard_gradients: &[Vec<f32>],
    ) -> f64 {
        if data_gradient.is_empty() || shard_gradients.is_empty() {
            return 0.0;
        }

        let mut total_influence = 0.0f64;
        let mut matches = 0;

        for shard_grad in shard_gradients {
            let sim = cosine_similarity(data_gradient, shard_grad);

            if sim >= self.similarity_threshold as f32 {
                total_influence += sim as f64;
                matches += 1;
            }
        }

        if matches == 0 {
            return 0.0;
        }

        let influence = total_influence / shard_gradients.len() as f64;

        influence.clamp(0.0, 1.0)
    }
}

/// Similaridade cosseno entre dois vetores
pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let min_len = a.len().min(b.len());
    if min_len == 0 {
        return 0.0;
    }

    let mut dot = 0.0f64;
    let mut norm_a = 0.0f64;
    let mut norm_b = 0.0f64;

    for i in 0..min_len {
        let ai = a[i] as f64;
        let bi = b[i] as f64;
        dot += ai * bi;
        norm_a += ai * ai;
        norm_b += bi * bi;
    }

    if norm_a == 0.0 || norm_b == 0.0 {
        return 0.0;
    }

    (dot / (norm_a.sqrt() * norm_b.sqrt())) as f32
}
