use arkhe_entropy_oracle::shannon_entropy;

pub fn fetch_entropy(data: &[u8]) -> f64 {
    shannon_entropy(data)
}
