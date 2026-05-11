use crate::ast::uast::UAST;

pub struct Transpiler {
    target_language: String,
}

impl Transpiler {
    pub fn new(target_language: &str, _config: TranspileConfig) -> Self {
        Self { target_language: target_language.to_string() }
    }

    pub fn transpile(&mut self, _uast: &UAST) -> Result<crate::transpile::TranspileResult, String> {
        Ok(crate::transpile::TranspileResult {
            code: "transpiled code".to_string(),
            target_language: self.target_language.clone(),
            line_map: vec![],
            metrics: crate::transpile::TranspileMetrics::default(),
            ast_delta: None,
        })
    }
}

pub struct TranspileConfig {}

impl Default for TranspileConfig {
    fn default() -> Self { Self {} }
}
