use serde::{Serialize, Deserialize};

/// Validador FAIR
pub struct FAIRValidator;

#[derive(Debug, Serialize, Deserialize)]
pub struct FAIRMetrics {
    pub findable: f64,
    pub accessible: f64,
    pub interoperable: f64,
    pub reusable: f64,
    pub overall: f64,
}

impl FAIRValidator {
    pub fn validate(dataset: &[u8], metadata: &serde_json::Value) -> FAIRMetrics {
        FAIRMetrics {
            findable: Self::score_findable(metadata),
            accessible: Self::score_accessible(dataset, metadata),
            interoperable: Self::score_interoperable(metadata),
            reusable: Self::score_reusable(metadata),
            overall: 0.0,
        }
    }

    fn score_findable(metadata: &serde_json::Value) -> f64 {
        let mut score = 0.0;
        if metadata.get("title").is_some() { score += 0.25; }
        if metadata.get("identifier").is_some() { score += 0.25; }
        if metadata.get("description").is_some() { score += 0.25; }
        if metadata.get("keywords").is_some() { score += 0.25; }
        score
    }

    fn score_accessible(dataset: &[u8], metadata: &serde_json::Value) -> f64 {
        // Verificar se há protocolo de acesso definido
        if !dataset.is_empty() && metadata.get("access_protocol").is_some() { 1.0 } else { 0.5 }
    }

    fn score_interoperable(metadata: &serde_json::Value) -> f64 {
        if metadata.get("format").is_some() && metadata.get("vocabulary").is_some() { 1.0 } else { 0.3 }
    }

    fn score_reusable(metadata: &serde_json::Value) -> f64 {
        if metadata.get("license").is_some() && metadata.get("provenance").is_some() { 1.0 } else { 0.4 }
    }
}
