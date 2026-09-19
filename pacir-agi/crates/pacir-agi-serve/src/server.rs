use crate::expert_cache::ExpertCache;
use pacir_agi_core::{ArkheResult, Router};
pub struct InferenceServer {
    router: Router,
    cache: ExpertCache,
}
impl InferenceServer {
    pub fn new(router: Router, cache_size: usize) -> Self {
        Self {
            router,
            cache: ExpertCache::new(cache_size),
        }
    }
    pub async fn infer_token(&mut self, embedding: &[f32]) -> ArkheResult<Vec<f32>> {
        let mut outputs = Vec::new();
        for id in self.router.route(embedding) {
            let expert = self.cache.get_or_fetch(id as u64).await?;
            outputs.push(
                expert
                    .iter()
                    .zip(embedding)
                    .map(|(a, b)| a * b)
                    .sum::<f32>(),
            );
        }
        Ok(vec![
            outputs.iter().sum::<f32>() / outputs.len().max(1) as f32,
        ])
    }
}
