use crate::temporal::art_block::ArtBlockRegistry;
use crate::types::StyleEmbedding;
use crate::errors::QArtError;

/// Detecta tendências estilísticas a partir dos embeddings recentes.
pub struct TrendDetector {
    window_blocks: usize,
}

impl TrendDetector {
    pub fn new(window_blocks: usize) -> Self {
        Self { window_blocks }
    }

    /// Calcula o embedding médio da janela temporal e retorna a direção de movimento.
    pub fn detect_trend(
        &self,
        registry: &ArtBlockRegistry,
        current_block: u64,
    ) -> Result<StyleEmbedding, QArtError> {
        let start = current_block.saturating_sub(self.window_blocks as u64);
        let blocks = registry.query_blocks_between(start, current_block)?;
        if blocks.is_empty() { return Err(QArtError::InfluenceError("no data".into())); }

        let dim = blocks[0].fingerprint.style_embedding.dim;
        let mut avg = vec![0.0f32; dim];
        for block in &blocks {
            for (i, &v) in block.fingerprint.style_embedding.vector.iter().enumerate() {
                avg[i] += v;
            }
        }
        for v in &mut avg { *v /= blocks.len() as f32; }
        Ok(StyleEmbedding { dim, vector: avg })
    }
}
