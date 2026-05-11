use arkhe_zklib::ZKProof;

pub struct ForceConvergenceProof {
    pub n_segments: usize,
    pub max_condition_number: f64,
    pub pulling_region_valid: bool,
    pub zk_circuit: ZKProof,
}
