// ============================================================================
// ARKHE P³ — TemporalHashChain Integration Hooks
// ============================================================================
// Hooks para registro automático de UAST no ledger temporal ARKHE.
// Cada parse gera um bloco com: hash do código, hash da UAST,
// metadados semânticos, e prova de integridade.
// ============================================================================

use crate::ast::uast::{UAST, NodeId, NodeKind};
use sha3::{Digest, Sha3_256};
use serde::{Serialize, Deserialize};
use std::sync::Arc;
use std::collections::HashMap;

// Mock temporal structs for parser-core integration
pub mod mock_temporal {
    use super::*;
    pub struct TemporalHashChain {}
    impl TemporalHashChain {
        pub fn append_message(&self, _msg: TemporalMessage, _report: ConsistencyReport) -> Result<u64, String> {
            Ok(0)
        }
        pub fn query_events_by_content(&self, _query: &str) -> Result<Vec<TemporalEvent>, String> {
            Ok(vec![])
        }
    }

    pub struct TemporalMessage {
        pub id: String,
        pub payload: String,
        pub source_node: String,
        pub namespace: String,
        pub signature: Option<Vec<u8>>,
    }
    impl TemporalMessage {
        pub fn new(id: String, payload: String, source_node: String, namespace: String, signature: Option<Vec<u8>>) -> Self {
            Self { id, payload, source_node, namespace, signature }
        }
    }

    pub struct TemporalConsistencyOracle {}
    impl TemporalConsistencyOracle {
        pub fn evaluate(&self, _msg: &TemporalMessage) -> ConsistencyReport {
            ConsistencyReport {
                consistent: true,
                score: 1.0,
                checks: HashMap::new(),
                violations: vec![],
                paradox_type: None,
                quantum_coherent: true,
                solar_coherent: true,
                galactic_coherent: true,
                observer_distance_au: 0.0,
            }
        }
    }

    pub struct ConsistencyReport {
        pub consistent: bool,
        pub score: f64,
        pub checks: HashMap<String, bool>,
        pub violations: Vec<String>,
        pub paradox_type: Option<String>,
        pub quantum_coherent: bool,
        pub solar_coherent: bool,
        pub galactic_coherent: bool,
        pub observer_distance_au: f64,
    }

    pub struct TemporalEvent {
        pub block_id: u64,
        pub timestamp: u64,
        pub payload: Option<String>,
    }
}

use mock_temporal::*;

pub fn current_nanos() -> u64 {
    std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos() as u64
}

/// Payload canônico para registro de código no ledger
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CodeRegistrationPayload {
    /// Hash SHA3-256 do código fonte original
    pub source_hash_hex: String,
    /// Hash SHA3-256 da UAST gerada
    pub uast_hash_hex: String,
    /// Linguagem detectada
    pub language: String,
    /// Dialeto (se aplicável)
    pub dialect: Option<String>,
    /// Métricas da UAST
    pub uast_metrics: UASTMetrics,
    /// Score do Oracle semântico
    pub oracle_score: Option<f64>,
    /// Timestamp em nanossegundos
    pub timestamp_ns: u64,
    /// Hash da identidade do autor (opcional)
    pub author_hash: Option<String>,
    /// Metadados extras
    pub metadata: std::collections::HashMap<String, serde_json::Value>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct UASTMetrics {
    pub node_count: usize,
    pub max_depth: usize,
    pub edge_count: usize,
    pub function_count: usize,
    pub class_count: usize,
    pub import_count: usize,
}

/// Registrador de código no TemporalHashChain
pub struct CodeTemporalRegistrar {
    ledger: Arc<TemporalHashChain>,
    oracle: Option<Arc<TemporalConsistencyOracle>>,
    node_id: String,
    auto_register: bool,
}

impl CodeTemporalRegistrar {
    /// Cria novo registrador
    pub fn new(
        ledger: Arc<TemporalHashChain>,
        oracle: Option<Arc<TemporalConsistencyOracle>>,
        node_id: String,
    ) -> Self {
        Self {
            ledger,
            oracle,
            node_id,
            auto_register: true,
        }
    }

    /// Habilita/desabilita registro automático
    pub fn set_auto_register(&mut self, enabled: bool) {
        self.auto_register = enabled;
    }

    /// Registra UAST no ledger temporal
    pub fn register_uast(
        &self,
        uast: &UAST,
        source_code: &str,
        language: &str,
        dialect: Option<&str>,
        author: Option<&[u8]>,
        metadata: Option<std::collections::HashMap<String, serde_json::Value>>,
    ) -> Result<RegistrationResult, RegistrationError> {
        // 1. Calcular hashes
        let source_hash = Sha3_256::digest(source_code.as_bytes());
        let uast_hash = uast.compute_hash();

        // 2. Coletar métricas da UAST
        let metrics = UASTMetrics {
            node_count: uast.node_count(),
            max_depth: 0, // Simplified for now
            edge_count: uast.nodes.values().map(|n| n.children.len()).sum(),
            function_count: uast.nodes.values()
                .filter(|n| matches!(n.kind, NodeKind::DeclFunction))
                .count(),
            class_count: 0, // NodeKind::DeclClass missing in simplified uast
            import_count: 0,
        };

        // 3. Avaliar via Oracle se disponível
        let oracle_score = if let Some(ref oracle) = self.oracle {
            // Criar mensagem temporal para avaliação
            let msg = TemporalMessage::new(
                format!("code-parse-{}", hex::encode(&uast_hash[..8])),
                serde_json::json!({
                    "language": language,
                    "dialect": dialect,
                    "metrics": metrics,
                }).to_string(),
                self.node_id.clone(),
                "ARKHE-PARSER".to_string(),
                author.map(|a| a.to_vec()),
            );
            let report = oracle.evaluate(&msg);
            Some(report.score)
        } else {
            None
        };

        // 4. Construir payload
        let payload = CodeRegistrationPayload {
            source_hash_hex: hex::encode(source_hash),
            uast_hash_hex: hex::encode(&uast_hash),
            language: language.to_string(),
            dialect: dialect.map(String::from),
            uast_metrics: metrics,
            oracle_score,
            timestamp_ns: current_nanos(),
            author_hash: author.map(|a| hex::encode(Sha3_256::digest(a))),
            metadata: metadata.unwrap_or_default(),
        };

        let payload_str = serde_json::to_string(&payload).map_err(|e|
            RegistrationError::Serialization(e.to_string()))?;

        // 5. Registrar no ledger
        let ledger_result = self.ledger.append_message(
            TemporalMessage::new(
                format!("code-{}", hex::encode(&uast_hash[..8])),
                payload_str.clone(),
                self.node_id.clone(),
                "ARKHE-PARSER".to_string(),
                author.map(|a| a.to_vec()),
            ),
            // Report simulado (em produção: usar resultado real do oracle)
            ConsistencyReport {
                consistent: true,
                score: oracle_score.unwrap_or(1.0),
                checks: Default::default(),
                violations: vec![],
                paradox_type: None,
                quantum_coherent: false,
                solar_coherent: false,
                galactic_coherent: false,
                observer_distance_au: 0.0,
            },
        );

        let block_id = match ledger_result {
            Ok(id) => id,
            Err(e) => {
                // Offline fallback
                eprintln!("Warning: Ledger registration failed, using offline fallback: {}", e);
                let _ = std::fs::write(".arkhe_offline_queue", format!("{}\n", payload_str));
                0 // Mock block ID
            }
        };

        Ok(RegistrationResult {
            block_id,
            source_hash: source_hash.to_vec(),
            uast_hash: uast_hash.to_vec(),
            oracle_score,
            timestamp_ns: payload.timestamp_ns,
        })
    }

    /// Consulta histórico de versões de um código
    pub fn query_code_history(
        &self,
        source_hash: &[u8],
    ) -> Result<Vec<CodeVersionEntry>, RegistrationError> {
        let hex_hash = hex::encode(source_hash);

        // Buscar eventos no ledger por hash de código
        let events = self.ledger.query_events_by_content(&format!(
            r#"{{"source_hash_hex": "{}"}}"#,
            hex_hash
        )).map_err(|e| RegistrationError::Ledger(e.to_string()))?;

        let mut versions = Vec::new();
        for event in events {
            if let Some(payload_str) = event.payload {
                if let Ok(payload) = serde_json::from_str::<CodeRegistrationPayload>(&payload_str) {
                    versions.push(CodeVersionEntry {
                        block_id: event.block_id,
                        timestamp: event.timestamp,
                        language: payload.language,
                        dialect: payload.dialect,
                        uast_hash: payload.uast_hash_hex,
                        oracle_score: payload.oracle_score,
                        metrics: payload.uast_metrics,
                    });
                }
            }
        }

        Ok(versions)
    }

    /// Hook: chamar automaticamente após parse bem-sucedido
    pub fn on_parse_complete(
        &self,
        uast: &UAST,
        source: &str,
        language: &str,
        dialect: Option<&str>,
        author: Option<&[u8]>,
    ) -> Result<(), RegistrationError> {
        if !self.auto_register {
            return Ok(());
        }

        let _result = self.register_uast(uast, source, language, dialect, author, None)?;
        Ok(())
    }
}

/// Resultado de registro
#[derive(Clone, Debug)]
pub struct RegistrationResult {
    pub block_id: u64,
    pub source_hash: Vec<u8>,
    pub uast_hash: Vec<u8>,
    pub oracle_score: Option<f64>,
    pub timestamp_ns: u64,
}

/// Entrada de versão de código
#[derive(Clone, Debug)]
pub struct CodeVersionEntry {
    pub block_id: u64,
    pub timestamp: u64,
    pub language: String,
    pub dialect: Option<String>,
    pub uast_hash: String,
    pub oracle_score: Option<f64>,
    pub metrics: UASTMetrics,
}

#[derive(Debug, thiserror::Error)]
pub enum RegistrationError {
    #[error("Erro no ledger: {0}")]
    Ledger(String),
    #[error("Erro de serialização: {0}")]
    Serialization(String),
    #[error("Oracle rejeitou: score={0}, paradox={1:?}")]
    OracleRejected(f64, Option<String>),
}
