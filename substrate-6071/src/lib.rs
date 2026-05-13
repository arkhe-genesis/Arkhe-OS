pub struct QipInfluence;

impl QipInfluence {
    pub fn new() -> Self {
        Self
    }

    pub fn compute_influence_with_entropy(
        &self,
        oracle: &arkhe_entropy_oracle::EntropyOracle,
        gradients: &[f64],
    ) -> f64 {
    pub fn compute_influence_with_entropy(&self, oracle: &arkhe_entropy_oracle::EntropyOracle, gradients: &[f64]) -> f64 {
        use arkhe_entropy_oracle::QipInfluenceEntropy;
        oracle.influence_entropy(gradients)
    }
}
pub mod qip4devs;
