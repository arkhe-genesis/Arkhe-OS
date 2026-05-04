use std::collections::HashMap;
use bumpalo::Bump;
use plank_hir::{HirExpr, HirLiteral};

#[derive(Clone, Debug)]
pub enum ConstValue {
    U256(ethnum::u256),
    Bool(bool),
    Bytes32([u8; 32]),
}

pub enum ComptimeError {
    UndefinedConst(String),
    RuntimeOnly(String),
}

pub struct ComptimeEvaluator<'a> {
    pub arena: &'a Bump,
    pub const_values: HashMap<String, ConstValue>,
}

impl<'a> ComptimeEvaluator<'a> {
    pub fn new(arena: &'a Bump) -> Self {
        Self {
            arena,
            const_values: HashMap::new(),
        }
    }

    pub fn eval(&mut self, expr: &HirExpr) -> Result<ConstValue, ComptimeError> {
        match expr {
            HirExpr::Literal(lit) => match lit {
                HirLiteral::U256(n) => Ok(ConstValue::U256(*n)),
                HirLiteral::Bool(b) => Ok(ConstValue::Bool(*b)),
            },
            HirExpr::Identifier(name) => self.const_values.get(name)
                .cloned()
                .ok_or(ComptimeError::UndefinedConst(name.clone())),
            _ => Err(ComptimeError::RuntimeOnly("Complex expression".to_string())),
        }
    }
}
