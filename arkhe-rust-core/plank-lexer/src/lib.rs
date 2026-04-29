use bumpalo::Bump;

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Token<'a> {
    // Palavras-chave do Scaffold
    Const,
    Fn,
    If,
    Else,
    Void,
    Bool,
    U256,
    Bytes32,

    // Builtins EVM (prefixados com @)
    EvmSload,
    EvmSstore,
    EvmKeccak256,
    EvmEmitLog,
    EvmAddress,
    EvmTimestamp,
    EvmReturn,

    // Literais
    IntLiteral(ethnum::u256),
    HexLiteral(&'a [u8]),
    StringLiteral(&'a str),

    // Identificadores
    Identifier(&'a str),

    // Delimitadores
    LParen, RParen, LBrace, RBrace, LBracket, RBracket,
    Semicolon, Colon, Comma, Arrow,
    Assign, Plus, Minus, Star, Slash, Percent,
    Eq, Ne, Lt, Gt, Le, Ge,

    // Especiais
    At,        // @ para builtins
    Hash,      // # para comptime
    Dot,       // . para acesso

    EOF,
}

pub struct Lexer<'a> {
    input: &'a str,
    pos: usize,
    arena: &'a Bump,
}

impl<'a> Lexer<'a> {
    pub fn new(input: &'a str, arena: &'a Bump) -> Self {
        Self { input, pos: 0, arena }
    }

    pub fn tokenize_all(&mut self) -> Vec<Token<'a>> {
        let mut tokens = Vec::new();
        loop {
            let tok = self.next_token();
            tokens.push(tok);
            if tok == Token::EOF {
                break;
            }
        }
        tokens
    }

    pub fn next_token(&mut self) -> Token<'a> {
        self.skip_whitespace();

        let c = match self.peek_char() {
            None => return Token::EOF,
            Some(c) => c,
        };

        match c {
            '@' => { self.advance(); self.evm_builtin() }
            '#' => { self.advance(); Token::Hash }
            '0'..='9' => self.number(),
            'a'..='z' | 'A'..='Z' | '_' => self.identifier(),
            '"' => self.string(),
            '.' => { self.advance(); Token::Dot }
            '(' => { self.advance(); Token::LParen }
            ')' => { self.advance(); Token::RParen }
            '{' => { self.advance(); Token::LBrace }
            '}' => { self.advance(); Token::RBrace }
            '[' => { self.advance(); Token::LBracket }
            ']' => { self.advance(); Token::RBracket }
            ';' => { self.advance(); Token::Semicolon }
            ':' => { self.advance(); Token::Colon }
            ',' => { self.advance(); Token::Comma }
            '+' => { self.advance(); Token::Plus }
            '-' => {
                self.advance();
                if self.peek_char() == Some('>') {
                    self.advance();
                    Token::Arrow
                } else {
                    Token::Minus
                }
            }
            '*' => { self.advance(); Token::Star }
            '/' => {
                self.advance();
                if self.peek_char() == Some('/') {
                    while let Some(c) = self.peek_char() {
                        if c == '\n' { break; }
                        self.advance();
                    }
                    self.next_token()
                } else {
                    Token::Slash
                }
            }
            '%' => { self.advance(); Token::Percent }
            '=' => {
                self.advance();
                if self.peek_char() == Some('=') {
                    self.advance();
                    Token::Eq
                } else {
                    Token::Assign
                }
            }
            '!' => {
                self.advance();
                if self.peek_char() == Some('=') {
                    self.advance();
                    Token::Ne
                } else {
                    panic!("Unexpected character '!'");
                }
            }
            '<' => {
                self.advance();
                if self.peek_char() == Some('=') {
                    self.advance();
                    Token::Le
                } else {
                    Token::Lt
                }
            }
            '>' => {
                self.advance();
                if self.peek_char() == Some('=') {
                    self.advance();
                    Token::Ge
                } else {
                    Token::Gt
                }
            }
            _ => panic!("Unexpected character: {}", c),
        }
    }

    fn skip_whitespace(&mut self) {
        while let Some(c) = self.peek_char() {
            if c.is_whitespace() {
                self.advance();
            } else {
                break;
            }
        }
    }

    fn peek_char(&self) -> Option<char> {
        self.input[self.pos..].chars().next()
    }

    fn advance(&mut self) {
        if let Some(c) = self.peek_char() {
            self.pos += c.len_utf8();
        }
    }

    fn read_identifier(&mut self) -> &'a str {
        let start = self.pos;
        while let Some(c) = self.peek_char() {
            if c.is_alphanumeric() || c == '_' {
                self.advance();
            } else {
                break;
            }
        }
        &self.input[start..self.pos]
    }

    fn identifier(&mut self) -> Token<'a> {
        let ident = self.read_identifier();
        match ident {
            "const" => Token::Const,
            "fn" => Token::Fn,
            "if" => Token::If,
            "else" => Token::Else,
            "void" => Token::Void,
            "bool" => Token::Bool,
            "u256" => Token::U256,
            "bytes32" => Token::Bytes32,
            _ => Token::Identifier(ident),
        }
    }

    fn evm_builtin(&mut self) -> Token<'a> {
        let ident = self.read_identifier();
        match ident {
            "evm_sload" => Token::EvmSload,
            "evm_sstore" => Token::EvmSstore,
            "evm_keccak256" => Token::EvmKeccak256,
            "evm_emit_log" => Token::EvmEmitLog,
            "evm_address" => Token::EvmAddress,
            "evm_timestamp" => Token::EvmTimestamp,
            "evm_return" => Token::EvmReturn,
            _ => panic!("Builtin desconhecido: @{}", ident),
        }
    }

    fn number(&mut self) -> Token<'a> {
        let start = self.pos;
        let mut is_hex = false;

        if self.peek_char() == Some('0') {
            self.advance();
            if self.peek_char() == Some('x') {
                self.advance();
                is_hex = true;
            }
        }

        while let Some(c) = self.peek_char() {
            if (is_hex && c.is_ascii_hexdigit()) || (!is_hex && c.is_ascii_digit()) {
                self.advance();
            } else {
                break;
            }
        }

        let num_str = &self.input[start..self.pos];
        let val = if is_hex {
            ethnum::u256::from_str_radix(&num_str[2..], 16).unwrap()
        } else {
            num_str.parse::<ethnum::u256>().unwrap()
        };
        Token::IntLiteral(val)
    }

    fn string(&mut self) -> Token<'a> {
        self.advance(); // skip "
        let start = self.pos;
        while let Some(c) = self.peek_char() {
            if c == '"' {
                break;
            }
            self.advance();
        }
        let s = &self.input[start..self.pos];
        self.advance(); // skip "
        Token::StringLiteral(s)
    }
}
