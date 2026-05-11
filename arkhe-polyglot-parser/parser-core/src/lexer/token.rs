#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Token {
    pub kind: TokenKind,
    pub line: u32,
    pub column: u32,
    pub length: usize,
    pub text: String,
}

impl Token {
    pub fn new(kind: TokenKind, line: u32, column: u32, length: usize) -> Self {
        Self { kind, line, column, length, text: String::new() }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum TokenKind {
    KwIf, KwElse, KwWhile, KwFor, KwFn, KwReturn, Identifier,
    LitInteger, LitString, OpArithPlus, DelLParen, DelRParen, Eof, Unknown(char),
}
