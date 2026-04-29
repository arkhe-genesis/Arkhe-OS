pub enum HirExpr {
    Literal(HirLiteral),
    Identifier(String),
}

pub enum HirLiteral {
    U256(ethnum::u256),
    Bool(bool),
}
