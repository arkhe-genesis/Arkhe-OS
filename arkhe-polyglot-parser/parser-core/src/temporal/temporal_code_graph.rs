use crate::ast::uast::UAST;

#[derive(Clone, Debug, Default)]
pub struct CodeDelta {
    pub changes: usize,
}

pub struct TemporalCodeGraph {}

impl TemporalCodeGraph {
    pub fn new() -> Self { Self {} }

    pub fn record_parse(&mut self, _uast: &UAST, _language: &str) {
        // Log temporal code
    }

    pub fn compute_delta(&self, _new_uast: &UAST) -> Option<CodeDelta> {
        Some(CodeDelta { changes: 0 })
    }

    pub fn compute_temporal_delta(&self, _old: &str, _new: &str) -> Option<CodeDelta> {
        Some(CodeDelta { changes: 0 })
    }
}
