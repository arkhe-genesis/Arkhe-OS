use rand::seq::SliceRandom;
use std::collections::HashMap;
use rand::prelude::*;
use rand::rngs::StdRng;;
use rayon::prelude::*;
use tracing::{debug, trace};

use crate::types::InfluenceResult;

/// Calculador de Shapley Values
pub struct ShapleyCalculator {
    /// Número de amostras de permutação
    num_samples: usize,
}

impl ShapleyCalculator {
    /// Criar novo calculador
    pub fn new(num_samples: usize) -> Self {
        Self { num_samples }
    }

    pub fn compute(&mut self, marginal_contributions: &[f64]) -> (f64, u128) {
        let start = std::time::Instant::now();

        if marginal_contributions.is_empty() {
            return (0.0, 0);
        }

        let n = marginal_contributions.len();

        if n == 1 {
            return (marginal_contributions[0].clamp(0.0, 1.0), start.elapsed().as_micros());
        }

        let mut total_shapley = vec![0.0f64; n];
        let mut rng = StdRng::from_entropy();
        let mut indices: Vec<usize> = (0..n).collect();

        for _sample in 0..self.num_samples {
            indices.shuffle(&mut rng);

            let mut cumulative_value = 0.0f64;

            for (position, &idx) in indices.iter().enumerate() {
                let new_value = cumulative_value + marginal_contributions[idx];
                let marginal = new_value - cumulative_value;

                total_shapley[idx] += marginal / n as f64;

                cumulative_value = new_value;
            }
        }

        let normalization = 1.0 / self.num_samples as f64;
        for shapley in &mut total_shapley {
            *shapley *= normalization;
        }

        let mean_shapley: f64 = total_shapley.iter().sum::<f64>() / n as f64;

        let elapsed = start.elapsed().as_micros();

        (mean_shapley.clamp(0.0, 1.0), elapsed)
    }
}
