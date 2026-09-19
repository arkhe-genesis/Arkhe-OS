#[derive(Debug, Clone)]
pub struct Router {
    routing_table: Vec<f32>,
    embedding_dim: usize,
    top_k: usize,
}
impl Router {
    pub fn new(routing_table: Vec<f32>, embedding_dim: usize, top_k: usize) -> Self {
        Self {
            routing_table,
            embedding_dim,
            top_k,
        }
    }
    pub fn route(&self, embedding: &[f32]) -> Vec<usize> {
        if self.embedding_dim == 0 || embedding.len() != self.embedding_dim {
            return Vec::new();
        }
        let mut scores: Vec<_> = self
            .routing_table
            .chunks_exact(self.embedding_dim)
            .enumerate()
            .map(|(i, weights)| {
                (
                    i,
                    weights
                        .iter()
                        .zip(embedding)
                        .map(|(a, b)| a * b)
                        .sum::<f32>(),
                )
            })
            .collect();
        scores.sort_by(|a, b| b.1.total_cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
        scores
            .into_iter()
            .take(self.top_k)
            .map(|(i, _)| i)
            .collect()
    }
    pub fn table_hash(&self) -> String {
        blake3::hash(
            &self
                .routing_table
                .iter()
                .flat_map(|value| value.to_le_bytes())
                .collect::<Vec<_>>(),
        )
        .to_hex()
        .to_string()
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn routes_top_score() {
        assert_eq!(
            Router::new(vec![1., 0., 0., 1.], 2, 1).route(&[1., 0.]),
            vec![0]
        );
    }
}
