use super::lexer::Token;

#[derive(Debug)]
pub enum Expr {
    Number(u64),
    Identifier(String),
    BinaryOp(Box<Expr>, String, Box<Expr>),
    BuiltinCall(String, Vec<Expr>),
}

#[derive(Debug)]
pub enum Stmt {
    VarDecl(String, Expr),
    ConstDecl(String, Expr),
    FunctionDecl(String, Vec<(String, String)>, String, Vec<Stmt>),
    If(Expr, Vec<Stmt>, Option<Vec<Stmt>>),
    Return(Expr),
}

pub struct PlankParser {
    tokens: Vec<Token>,
    pos: usize,
}

impl PlankParser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, pos: 0 }
    }

    pub fn parse(&mut self) -> Result<Vec<Stmt>, String> {
        let mut stmts = Vec::new();
        while self.pos < self.tokens.len() {
            stmts.push(self.parse_stmt()?);
        }
        Ok(stmts)
    }

    fn parse_stmt(&mut self) -> Result<Stmt, String> {
        let token = &self.tokens[self.pos];
        match token {
            Token::Const => {
                self.pos += 1;
                if let Token::Identifier(name) = &self.tokens[self.pos] {
                    let name = name.clone();
                    self.pos += 1;
                    self.expect(Token::Colon)?;
                    self.pos += 1; // Skip type
                    self.expect(Token::Assign)?;
                    self.pos += 1;
                    let expr = self.parse_expr()?;
                    self.expect(Token::Semicolon)?;
                    self.pos += 1;
                    Ok(Stmt::ConstDecl(name, expr))
                } else {
                    Err("Expected identifier after const".to_string())
                }
            },
            Token::Fn => {
                self.pos += 1;
                if let Token::Identifier(name) = &self.tokens[self.pos] {
                    let name = name.clone();
                    self.pos += 1;
                    self.expect(Token::OpenParen)?;
                    self.pos += 1;
                    // Skip params for now
                    self.expect(Token::CloseParen)?;
                    self.pos += 1;
                    // Skip return type
                    self.pos += 1;
                    self.expect(Token::OpenBrace)?;
                    self.pos += 1;
                    let mut body = Vec::new();
                    while self.tokens[self.pos] != Token::CloseBrace {
                        body.push(self.parse_stmt()?);
                    }
                    self.pos += 1;
                    Ok(Stmt::FunctionDecl(name, Vec::new(), "void".to_string(), body))
                } else {
                    Err("Expected identifier after fn".to_string())
                }
            },
            _ => Err(format!("Unexpected token in statement: {:?}", token)),
        }
    }

    fn parse_expr(&mut self) -> Result<Expr, String> {
        let token = &self.tokens[self.pos];
        match token {
            Token::Number(n) => {
                let val = *n;
                self.pos += 1;
                Ok(Expr::Number(val))
            },
            Token::Identifier(name) => {
                let name = name.clone();
                self.pos += 1;
                Ok(Expr::Identifier(name))
            },
            Token::Builtin(name) => {
                let name = name.clone();
                self.pos += 1;
                self.expect(Token::OpenParen)?;
                self.pos += 1;
                let mut args = Vec::new();
                while self.tokens[self.pos] != Token::CloseParen {
                    args.push(self.parse_expr()?);
                    if self.tokens[self.pos] == Token::Comma { self.pos += 1; }
                }
                self.pos += 1;
                Ok(Expr::BuiltinCall(name, args))
            },
            _ => Err(format!("Unexpected token in expression: {:?}", token)),
        }
    }

    fn expect(&self, token: Token) -> Result<(), String> {
        if self.pos < self.tokens.len() && self.tokens[self.pos] == token {
            Ok(())
        } else {
            Err(format!("Expected {:?}", token))
        }
    }
}
