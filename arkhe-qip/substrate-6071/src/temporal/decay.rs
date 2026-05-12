use std::collections::VecDeque;
use serde::{Serialize, Deserialize};

pub struct TemporalDecay {
    decay_factor: f64,
}

impl TemporalDecay {
    pub fn new(decay_factor: f64) -> Self {
        Self { decay_factor }
    }
}
