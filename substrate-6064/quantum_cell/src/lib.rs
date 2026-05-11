pub mod organelle_qpu;
pub mod hamiltonian;
pub mod decoherence;
pub mod types {
    #[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
    pub struct ProteinId(pub u64);

    #[derive(Debug, Clone)]
    pub struct ProteinConformation {
        pub data: Vec<f64>,
    }
}
