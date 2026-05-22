// quantum_ml/483-ensemble-aggregator/majority_vote.rs
use std::collections::HashMap;

/// 483-ENSEMBLE-AGGREGATOR - Majority vote aggregation in Rust.
pub struct EnsembleAggregator {
    weights: HashMap<usize, f64>,
}

impl EnsembleAggregator {
    pub fn new() -> Self {
        Self {
            weights: HashMap::new(),
        }
    }

    pub fn add_voter(&mut self, voter_id: usize, weight: f64) {
        self.weights.insert(voter_id, weight);
    }

    pub fn aggregate(&self, votes: &HashMap<usize, i32>) -> Result<(i32, f64), &'static str> {
        if votes.is_empty() {
            return Err("No votes provided");
        }

        let mut tally: HashMap<i32, f64> = HashMap::new();
        let mut total_weight = 0.0;

        for (voter_id, vote) in votes {
            let weight = self.weights.get(voter_id).unwrap_or(&1.0);
            *tally.entry(*vote).or_insert(0.0) += weight;
            total_weight += weight;
        }

        let mut best_vote = 0;
        let mut max_score = -1.0;

        for (vote, score) in tally {
            if score > max_score {
                max_score = score;
                best_vote = vote;
            }
        }

        let confidence = max_score / total_weight;
        Ok((best_vote, confidence))
    }
}
