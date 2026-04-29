#[derive(Debug, Clone, PartialEq)]
pub enum Token {
    Const,
    Let,
    Fn,
    If,
    Else,
    For,
    Void,
    U256,
    Bool,
    Bytes32,
    Identifier(String),
    Number(u64),
    StringLiteral(String),
    Assign,
    Plus,
    Minus,
    Asterisk,
    Slash,
    Equal,
    NotEqual,
    OpenParen,
    CloseParen,
    OpenBrace,
    CloseBrace,
    OpenBracket,
    CloseBracket,
    Comma,
    Colon,
    Semicolon,
    Builtin(String), // @evm_...
}

pub struct PlankLexer<'a> {
    source: &'a str,
}

impl<'a> PlankLexer<'a> {
    pub fn new(source: &'a str) -> Self {
        Self { source }
    }

    pub fn tokenize(&self) -> Result<Vec<Token>, String> {
        let mut tokens = Vec::new();
        // Basic lexer implementation for canonization
        // In a real scenario, this would use a regex or a state machine
        let mut chars = self.source.chars().peekable();

        while let Some(&c) = chars.peek() {
            match c {
                ' ' | '\t' | '\n' | '\r' => { chars.next(); },
                '/' => {
                    chars.next();
                    if let Some('/') = chars.peek() {
                        while let Some(&c) = chars.peek() {
                            if c == '\n' { break; }
                            chars.next();
                        }
                    } else {
                        tokens.push(Token::Slash);
                    }
                },
                '{' => { tokens.push(Token::OpenBrace); chars.next(); },
                '}' => { tokens.push(Token::CloseBrace); chars.next(); },
                '(' => { tokens.push(Token::OpenParen); chars.next(); },
                ')' => { tokens.push(Token::CloseParen); chars.next(); },
                '[' => { tokens.push(Token::OpenBracket); chars.next(); },
                ']' => { tokens.push(Token::CloseBracket); chars.next(); },
                '=' => {
                    chars.next();
                    if let Some('=') = chars.peek() {
                        tokens.push(Token::Equal);
                        chars.next();
                    } else {
                        tokens.push(Token::Assign);
                    }
                },
                '+' => { tokens.push(Token::Plus); chars.next(); },
                '-' => { tokens.push(Token::Minus); chars.next(); },
                '*' => { tokens.push(Token::Asterisk); chars.next(); },
                ',' => { tokens.push(Token::Comma); chars.next(); },
                ':' => { tokens.push(Token::Colon); chars.next(); },
                ';' => { tokens.push(Token::Semicolon); chars.next(); },
                '@' => {
                    chars.next();
                    let mut builtin = String::new();
                    while let Some(&c) = chars.peek() {
                        if c.is_alphanumeric() || c == '_' {
                            builtin.push(c);
                            chars.next();
                        } else {
                            break;
                        }
                    }
                    tokens.push(Token::Builtin(builtin));
                },
                '0'..='9' => {
                    let mut num_str = String::new();
                    while let Some(&c) = chars.peek() {
                        if c.is_digit(10) {
                            num_str.push(c);
                            chars.next();
                        } else {
                            break;
                        }
                    }
                    tokens.push(Token::Number(num_str.parse().unwrap()));
                },
                'a'..='z' | 'A'..='Z' | '_' => {
                    let mut ident = String::new();
                    while let Some(&c) = chars.peek() {
                        if c.is_alphanumeric() || c == '_' {
                            ident.push(c);
                            chars.next();
                        } else {
                            break;
                        }
                    }
                    match ident.as_str() {
                        "const" => tokens.push(Token::Const),
                        "let" => tokens.push(Token::Let),
                        "fn" => tokens.push(Token::Fn),
                        "if" => tokens.push(Token::If),
                        "else" => tokens.push(Token::Else),
                        "for" => tokens.push(Token::For),
                        "void" => tokens.push(Token::Void),
                        "u256" => tokens.push(Token::U256),
                        "bool" => tokens.push(Token::Bool),
                        "bytes32" => tokens.push(Token::Bytes32),
                        _ => tokens.push(Token::Identifier(ident)),
                    }
                },
                _ => { chars.next(); } // Skip unknown
            }
        }

        Ok(tokens)
    }
}
