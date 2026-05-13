use rand::prelude::*;
use rand::rngs::StdRng;;
use std::sync::Arc;
use tracing::trace;

/// Sampler Monte Carlo para estimativa de influência
pub struct MonteCarloSampler {
    num_samples: usize,
    similarity_threshold: f64,
    seed: std::sync::atomic::AtomicU64,
}

impl MonteCarloSampler {
    pub fn new(num_samples: usize, similarity_threshold: f64) -> Self {
        Self {
            num_samples,
            similarity_threshold,
            seed: std::sync::atomic::AtomicU64::new(42),
        }
    }

    pub fn sample(
        &self,
        similarities: &[f64],
    ) -> f64 {
        if similarities.is_empty() || self.num_samples == 0 {
            return 0.0;
        }

        let n = similarities.len();
        let current_seed = self.seed.fetch_add(self.num_samples as u64, std::sync::atomic::Ordering::Relaxed);
        let mut rng = StdRng::seed_from_u64(current_seed);
        let mut total_influence = 0.0f64;
        let mut valid_samples = 0;

        for _ in 0..self.num_samples {
            let mut subset_influence = 0.0f64;
            let mut subset_size = 0;

            for (i, &similarity) in similarities.iter().enumerate() {
                if rng.gen_bool(0.5) {
                    subset_influence += similarity;
                    subset_size += 1;
                }
            }

            if subset_size > 0 {
                let avg_similarity = subset_influence / subset_size as f64;

                if avg_similarity >= self.similarity_threshold {
                    total_influence += avg_similarity;
                    valid_samples += 1;
                }
            }
        }

        if valid_samples == 0 {
            return 0.0;
        }

        let probability = total_influence / valid_samples as f64;

        probability.clamp(0.0, 1.0)
    }
}
