use crate::lexer::token::{Token, TokenKind};

pub struct PolyglotLexer {}

impl PolyglotLexer {
    pub fn new() -> Self { Self {} }

    pub fn tokenize(&mut self, _source: &str, _grammar: &crate::grammar::Grammar) -> Result<Vec<Token>, String> {
        Ok(vec![Token::new(TokenKind::Eof, 1, 1, 0)])
    }
}
