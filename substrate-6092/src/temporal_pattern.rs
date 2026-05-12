pub struct TemporalPattern {}

impl Default for TemporalPattern {
    fn default() -> Self {
        Self::new()
    }
}

impl TemporalPattern {
    pub fn new() -> Self {
        Self {}
    }

    pub fn match_pattern(&self, _context: &serde_json::Value) -> (Vec<String>, f64) {
        (vec!["pay_royalty".to_string()], 0.8)
    }
}
