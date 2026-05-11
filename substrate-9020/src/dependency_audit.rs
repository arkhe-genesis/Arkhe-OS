use std::sync::Arc;
use crate::agent::SecurityAgent;

/// Analisa o grafo de dependências do workspace em busca de riscos.
pub struct DependencyAudit {
    agent: Arc<SecurityAgent>,
}

pub struct DependencyRisk {
    pub crate_name: String,
    pub vulnerability: Option<String>,
    pub risk_score: f64,
}

impl DependencyAudit {
    pub async fn audit_workspace(&self) -> Vec<DependencyRisk> {
        // Chama `cargo audit` e também consulta a base de dados de CVEs da ARKHE.
        todo!()
    }
}
