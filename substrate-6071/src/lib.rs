
pub struct QipInfluence;

impl QipInfluence {
    pub fn new() -> Self { Self }

    pub fn compute_influence_with_entropy(&self, oracle: &substrate_6070::EntropyOracle, gradients: &[f64]) -> f64 {
        use substrate_6070::QipInfluenceEntropy;
        oracle.influence_entropy(gradients)
    }
}
pub mod qip4devs;
