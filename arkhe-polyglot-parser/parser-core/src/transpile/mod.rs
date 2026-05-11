pub mod transpiler;

#[derive(Debug, Clone)]
pub struct TranspileResult {
    pub code: String,
    pub target_language: String,
    pub line_map: Vec<(usize, usize)>,
    pub metrics: TranspileMetrics,
    pub ast_delta: Option<String>,
}

#[derive(Debug, Clone, Default)]
pub struct TranspileMetrics {
    pub time_ms: u64,
    pub nodes_processed: usize,
}
pub mod type_safe_codegen;
