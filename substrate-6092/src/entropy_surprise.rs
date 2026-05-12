pub struct EntropySurprise {}

impl Default for EntropySurprise {
    fn default() -> Self {
        Self::new()
    }
}

impl EntropySurprise {
    pub fn new() -> Self {
        Self {}
    }

    pub fn surprise(&self, _context: &serde_json::Value) -> (Vec<String>, f64) {
        (vec!["pay_royalty".to_string()], 0.3)
    }
}
