pub mod compiler;

use thiserror::Error;

#[derive(Error, Debug, Clone)]
pub enum ArkheError {
    #[error("Geometric error: {0}")]
    GeometricError(String),
    #[error("Synchronization error: {0}")]
    SyncError(String),
}

#[derive(Clone, Debug, Copy, PartialEq)]
pub struct Multivector {
    pub data: [f64; 16],
}

impl Multivector {
    pub fn zero() -> Self {
        Self { data: [0.0; 16] }
    }

    pub fn from_scalar(s: f64) -> Self {
        let mut mv = Self::zero();
        mv.data[0] = s;
        return mv;
    }

    pub fn norm_squared(&self) -> f64 {
        self.data.iter().map(|&x| x * x).sum()
    }
}

#[derive(Clone, Debug, Copy, PartialEq)]
pub struct KuramotoOscillator {
    pub natural_frequency: f64,
    pub phase: f64,
    pub coupling: f64,
    pub local_coherence: f64,
}

impl KuramotoOscillator {
    pub fn new(natural_frequency: f64, phase: f64, coupling: f64) -> Self {
        Self {
            natural_frequency,
            phase,
            coupling,
            local_coherence: 0.0,
        }
    }

    pub fn order_contribution(&self) -> (f64, f64) {
        (self.phase.cos(), self.phase.sin())
    }
}
pub mod arkhe_oam_token_layer;
