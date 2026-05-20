//! Arkhe Compute Module
//!
//! PhiC workload computation

use crate::{ArkheError, PhiC};

/// Compute engine trait
pub trait ComputeEngine {
    fn compute_workload(
        &self,
        base: f64,
        complexity: f64,
        humility: f64,
    ) -> Result<PhiC, ArkheError>;
}

/// PhiC compute engine
pub struct PhiCComputeEngine;

impl ComputeEngine for PhiCComputeEngine {
    fn compute_workload(
        &self,
        base: f64,
        complexity: f64,
        humility: f64,
    ) -> Result<PhiC, ArkheError> {
        PhiC::compute_workload(base, complexity, humility)
    }
}

/// Complexity adapter for different workload types
pub struct ComplexityAdapter;

impl ComplexityAdapter {
    pub fn complexity_for(workload_type: &str) -> f64 {
        match workload_type {
            "inference" => 0.3,
            "training" => 0.6,
            "validation" => 0.45,
            "synthesis" => 0.75,
            "analysis" => 0.9,
            _ => 0.5,
        }
    }
}
