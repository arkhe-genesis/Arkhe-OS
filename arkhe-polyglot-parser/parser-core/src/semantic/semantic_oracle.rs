use crate::ast::uast::UAST;

#[derive(Clone, Debug, Default)]
pub struct SemanticReport {
    pub overall_score: f64,
    pub complexity_score: f64,
    pub security_score: f64,
    pub arkhe_compatibility: f64,
}

pub struct SemanticOracle {}

impl SemanticOracle {
    pub fn new() -> Self { Self {} }

    pub fn analyze(&self, _uast: &UAST) -> SemanticReport {
        SemanticReport {
            overall_score: 1.0,
            complexity_score: 0.5,
            security_score: 1.0,
            arkhe_compatibility: 1.0,
        }
    }
}
