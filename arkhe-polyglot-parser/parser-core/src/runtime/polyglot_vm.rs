use crate::ast::uast::UAST;

pub struct PolyglotVM {}

impl PolyglotVM {
    pub fn new() -> Self { Self {} }

    pub fn execute_uast(&mut self, _uast: &UAST) -> Result<(), String> {
        Ok(())
    }
}
