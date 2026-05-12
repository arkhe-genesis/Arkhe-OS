// ============================================================================
// ARKHE Ω-TEMP v5.6.0 — Universal Bug Bounty Hunter
// ============================================================================
//
// O primeiro caçador de bugs verdadeiramente universal.
// Ele não procura bugs em uma linguagem — ele procura bugs na COMPUTAÇÃO.
//
// Funcionalidades:
//   1. Análise estática multi-linguagem via UAST
//   2. Fuzzing dinâmico em sandbox seguro (Wasm)
//   3. Detecção de vulnerabilidades por ML embarcado (ONNX)
//   4. Rastreamento temporal de origem de bugs (Blame Chain)
//   5. Verificação formal de exploits com provas ZK
//   6. Sistema de bounties integrado com ARKHE
//   7. Relatórios automáticos com reprodução de exploits
//
// Pipeline:
//   Source → UAST → Static Analysis → ML Classification → Fuzz Verify → Report
//              ↓                                              ↓
//         Temporal Blame Chain                        Exploit Proof (ZK)
//              ↓                                              ↓
//         Causal Shield Check                        ARKHE Bounty Registration
//
// ============================================================================

#![cfg_attr(feature = "wasm-bindings", no_std)]
#![deny(missing_docs)]
#![warn(clippy::all, clippy::pedantic)]
#![allow(clippy::module_name_repetitions)]

// ============================================================================
// MÓDULOS PRINCIPAIS
// ============================================================================

/// Motor principal do caçador de bugs
pub mod hunter {
    pub mod scanner;
    pub mod analyzer;
    pub mod fuzzer;
    pub mod exploit_verify;
    pub mod severity;
}

/// Padrões de vulnerabilidade e bancos de dados
pub mod patterns {
    pub mod vulnerability_db;
    pub mod cwe_registry;
    pub mod owasp_top10;
    pub mod temporal_patterns;
    pub mod injection;
    pub mod crypto;
    pub mod memory;
    pub mod logic;
}

/// Motor de aprendizado de máquina
pub mod ml {
    pub mod feature_extractor;
    pub mod vulnerability_classifier;
    pub mod anomaly_detector;
    pub mod model;
}

/// Framework de auditoria e relatórios
pub mod audit {
    pub mod auditor;
    pub mod report;
    pub mod bounty;
    pub mod compliance;
}

/// Integração temporal — rastreamento de origem de bugs
pub mod temporal {
    pub mod bug_origin;
    pub mod blame_chain;
    pub mod regression_detector;
}

/// Provas formais de vulnerabilidade
pub mod proof {
    pub mod exploit_proof;
    pub mod zk_audit;
}

/// API para integração com CI/CD e dashboards
pub mod api {
    pub mod server;
    pub mod webhook;
}

// Re-exports principais
pub use hunter::scanner::VulnScanner;
pub use hunter::analyzer::VulnAnalyzer;
pub use hunter::fuzzer::VulnFuzzer;
pub use hunter::severity::{Severity, CVSSv3, VulnClass};
pub use audit::report::VulnReport;
pub use audit::bounty::BountyRegistry;
pub use patterns::cwe_registry::CWERegistry;
pub use temporal::blame_chain::BlameChain;

// ============================================================================
// TIPOS COMPARTILHADOS
// ============================================================================

/// Identificador único de vulnerabilidade ARKHE
#[derive(Clone, Debug, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct VulnId(String);

impl VulnId {
    pub fn new(source_file: &str, line: u32, rule_id: &str) -> Self {
        let content = format!("{}:{}:{}", source_file, line, rule_id);
        let hash = blake3::hash(content.as_bytes());
        Self(format!("VH-{}", &hash.to_hex()[..12]))
    }

    pub fn to_hex(&self) -> &str {
        &self.0
    }
}

/// Localização de vulnerabilidade no código fonte
#[derive(Clone, Debug, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct VulnLocation {
    pub file: String,
    pub line: u32,
    pub column: u32,
    pub end_line: u32,
    pub end_column: u32,
    pub function: Option<String>,
    pub module: Option<String>,
}

/// Representação de um bug encontrado
#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct Vulnerability {
    pub id: VulnId,
    pub cwe_id: String,
    pub owasp_category: Option<String>,
    pub severity: Severity,
    pub cvss_score: f32,
    pub title: String,
    pub description: String,
    pub location: VulnLocation,
    pub language: String,
    pub pattern_matched: String,
    pub exploitability: Exploitability,
    pub remediation: String,
    pub code_snippet: Option<String>,
    pub fix_suggestion: Option<String>,
    pub confidence: f64,
    pub ml_score: Option<f64>,
    pub temporal_info: Option<TemporalVulnInfo>,
    pub is_false_positive: bool,
    pub proof_available: bool,
}

/// Nível de explorabilidade
#[derive(Clone, Copy, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub enum Exploitability {
    NotExploitable,
    Low,
    Medium,
    High,
    Critical,
    ConfirmedExploit,
}

/// Informação temporal de vulnerabilidade
#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct TemporalVulnInfo {
    pub first_seen_version: u64,
    pub last_present_version: u64,
    pub introduced_by_commit: Option<String>,
    pub blame_author: Option<String>,
    pub lifespan_versions: u64,
    pub is_regression: bool,
}

/// Resultado da análise de um arquivo
#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct FileAnalysis {
    pub file: String,
    pub language: String,
    pub vulnerabilities: Vec<Vulnerability>,
    pub stats: AnalysisStats,
    pub scan_time_ms: u64,
}

/// Estatísticas de análise
#[derive(Clone, Debug, Default, serde::Serialize, serde::Deserialize)]
pub struct AnalysisStats {
    pub lines_scanned: u64,
    pub patterns_checked: u64,
    pub patterns_matched: u64,
    pub ml_inferences: u64,
    pub false_positives_filtered: u64,
    pub exploits_verified: u64,
    pub unique_cwes: usize,
    pub max_severity: Severity,
}

/// Configuração geral do caçador
#[derive(Clone, Debug)]
pub struct HunterConfig {
    pub enabled_scanners: Vec<String>,
    pub severity_threshold: Severity,
    pub max_depth: u32,
    pub enable_ml: bool,
    pub enable_fuzzing: bool,
    pub enable_temporal: bool,
    pub enable_proof: bool,
    pub timeout_per_file_secs: u64,
    pub max_file_size_mb: u64,
    pub concurrent_scans: usize,
    pub output_format: OutputFormat,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum OutputFormat {
    Json,
    Markdown,
    Sarif,
    Html,
    Mermaid,
}

impl Default for HunterConfig {
    fn default() -> Self {
        Self {
            enabled_scanners: vec![
                "static".into(),
                "pattern".into(),
                "ml".into(),
                "temporal".into(),
            ],
            severity_threshold: Severity::Medium,
            max_depth: 100,
            enable_ml: true,
            enable_fuzzing: false,
            enable_temporal: true,
            enable_proof: false,
            timeout_per_file_secs: 30,
            max_file_size_mb: 50,
            concurrent_scans: 8,
            output_format: OutputFormat::Json,
        }
    }
}
