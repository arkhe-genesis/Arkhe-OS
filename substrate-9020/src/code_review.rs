use crate::agent::SecurityAgent;
use std::sync::Arc;

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
    pub fn new(agent: Arc<SecurityAgent>) -> Self {
        Self { agent }
    }

    pub async fn review(&self, code: &str) -> Vec<ReviewResult> {
        let mut results = vec![];

        // Check for pull_request_target cache poisoning pattern
        if code.contains("pull_request_target") && code.contains("actions/cache@") {
            results.push(ReviewResult {
                location: "workflow.yml".to_string(),
                issue: "pull_request_target cache poisoning vulnerability".to_string(),
                severity: crate::agent::Severity::Critical,
                recommendation: Some("Este workflow permite que código de um fork acesse o cache do repositório base. Isso pode ser explorado para injetar payloads maliciosos no pipeline de build.".to_string()),
            });
        }

        results
    }
}
