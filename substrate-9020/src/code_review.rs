use std::sync::Arc;
use crate::agent::SecurityAgent;

/// Resultado de uma revisão de código agêntica.
pub struct ReviewResult {
    pub location: String,
    pub issue: String,
    pub severity: crate::agent::Severity,
    pub recommendation: Option<String>,
}

pub struct CodeReviewHarness {
    agent: Arc<SecurityAgent>,
}

impl CodeReviewHarness {
    pub async fn review(&self, code: &str) -> Vec<ReviewResult> {
        // Simula envio ao Continental Mind em modo cyber.
        vec![]
    }
}
