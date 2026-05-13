use logos::Logos;

#[derive(Logos, Debug, PartialEq, Clone)]
#[logos(skip r"[ \t\n\f]+")] // Ignore this regex pattern between tokens
#[logos(skip r"//.*")] // Ignore single line comments
#[logos(skip r"/\*[^*]*\*/")] // Ignore block comments
pub enum Token {
    // Keywords
    #[token("block")]
    Block,
    #[token("prove")]
    Prove,
    #[token("anchor")]
    Anchor,
    #[token("pay")]
    Pay,
    #[token("pretend")]
    Pretend,
    #[token("quantum")]
    Quantum,
    #[token("entropy")]
    Entropy,
    #[token("coherence")]
    Coherence,
    #[token("q_art")]
    QArt,
    #[token("vortex")]
    Vortex,
    #[token("orcid")]
    Orcid,
    #[token("pix")]
    Pix,
    #[token("multiversal")]
    Multiversal,
    #[token("let")]
    Let,
    #[token("fn")]
    Fn,
    #[token("if")]
    If,
    #[token("else")]
    Else,
    #[token("for")]
    For,
    #[token("in")]
    In,
    #[token("loop")]
    Loop,
    #[token("return")]
    Return,
    #[token("use")]
    Use,
    #[token("import")]
    Import,
    #[token("as")]
    As,
    #[token("from")]
    From,
    #[token("type")]
    Type,
    #[token("struct")]
    Struct,
    #[token("enum")]
    Enum,
    #[token("trait")]
    Trait,
    #[token("impl")]
    Impl,
    #[token("true")]
    True,
    #[token("false")]
    False,
    #[token("zk")]
    Zk,
    #[token("Secret")]
    SecretKw,
    #[token("Temporal")]
    TemporalKw,
    #[token("Qubit")]
    QubitKw,
    #[token("Influence")]
    InfluenceKw,
    #[token("EntropyKw")]
    EntropyKw,
    #[token("CoherenceKw")]
    CoherenceKw,
    #[token("block_id")]
    BlockId,
    #[token("linear")]
    LinearKw,
    #[token("mut")]
    Mut,
    #[token("pub")]
    Pub,
    #[token("self")]
    SelfKw,
    #[token("Self")]
    SelfTypeKw,
    #[token("where")]
    Where,
    #[token("match")]
    Match,

    // Types
    #[token("Int")]
    IntType,
    #[token("Float")]
    FloatType,
    #[token("Bool")]
    BoolType,
    #[token("String")]
    StringType,
    #[token("Byte")]
    ByteType,
    #[token("Unit")]
    UnitType,

    // Operators and Punctuation
    #[token("+")]
    Plus,
    #[token("-")]
    Minus,
    #[token("*")]
    Star,
    #[token("/")]
    Slash,
    #[token("==")]
    EqEq,
    #[token("!=")]
    NotEq,
    #[token("<")]
    Less,
    #[token(">")]
    Greater,
    #[token("<=")]
    LessEq,
    #[token(">=")]
    GreaterEq,
    #[token("=")]
    Eq,
    #[token("=>")]
    FatArrow,
    #[token("->")]
    Arrow,
    #[token(",")]
    Comma,
    #[token(";")]
    Semi,
    #[token(":")]
    Colon,
    #[token("::")]
    ColonColon,
    #[token(".")]
    Dot,
    #[token("(")]
    LParen,
    #[token(")")]
    RParen,
    #[token("{")]
    LBrace,
    #[token("}")]
    RBrace,
    #[token("[")]
    LBracket,
    #[token("]")]
    RBracket,
    #[token("#")]
    Hash,
    #[token("?")]
    Question,

    // Literals and Identifiers
    #[regex(r"[a-zA-Z_][a-zA-Z0-9_]*", |lex| lex.slice().to_string())]
    Ident(String),

    #[regex(r"([0-9]+|0x[0-9a-fA-F]+)", |lex| lex.slice().to_string())]
    IntLit(String),

    #[regex(r"[0-9]+\.[0-9]*", |lex| lex.slice().to_string())]
    FloatLit(String),

    #[regex(r#""[^"]*""#, |lex| lex.slice().to_string())]
    StringLit(String),

    #[regex(r#"b"[^"]*""#, |lex| lex.slice().to_string())]
    ByteLit(String),
}

pub fn lex(input: &str) -> Vec<Result<Token, ()>> {
    let mut lex = Token::lexer(input);
    let mut res = Vec::new();
    while let Some(tok) = lex.next() {
        res.push(tok);
    }
    res
}
