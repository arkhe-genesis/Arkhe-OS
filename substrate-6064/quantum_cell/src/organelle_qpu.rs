use std::collections::HashMap;
use crate::types::{ProteinId, ProteinConformation};

/// All organelles that receive a quantum register.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Organelle {
    Mitochondria,
    Microtubule,
    Nucleus,
    EndoplasmicReticulum,
    Golgi,
    Lysosome,
}

/// Configuration for one organelle's QPU.
pub struct OrganelleQPU {
    pub qubit_count: usize,          // number of virtual qubits
    pub tau_decoherence_fs: f64,     // decoherence time (femtoseconds)
    pub state: Vec<f64>,             // current probability amplitudes
}

/// The cellular QPU containing all organelle registers.
pub struct CellularQPU {
    /// Map from organelle to its register
    pub registers: HashMap<Organelle, OrganelleQPU>,
    /// Entangled protein states currently being folded
    pub protein_states: HashMap<ProteinId, ProteinConformation>,
}
