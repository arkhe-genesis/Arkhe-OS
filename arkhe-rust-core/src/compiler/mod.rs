pub mod lexer;
pub mod parser;
pub mod emitter;

pub struct PlankCompiler;

impl PlankCompiler {
    pub fn compile(source: &str) -> Result<Vec<u8>, String> {
        let tokens = lexer::PlankLexer::new(source).tokenize()?;
        let ast = parser::PlankParser::new(tokens).parse()?;
        let bytecode = emitter::EvmEmitter::new(ast).emit()?;
        Ok(bytecode)
    }
}
