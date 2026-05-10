pub mod semantic_oracle;

use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct SemanticInfo {
    pub type_info: Option<crate::ast::uast::TypeRef>,
}

#[derive(Clone, Debug)]
pub struct TypeEnvironment {}

#[derive(Clone, Debug)]
pub struct TypeConstraint {}

pub struct TypeInferencer {}

impl TypeInferencer {
    pub fn new() -> Self { Self {} }
    pub fn infer_types(&mut self, _uast: &mut crate::ast::uast::UAST) -> Result<(), String> {
        Ok(())
    }
}
