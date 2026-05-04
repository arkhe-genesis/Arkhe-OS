pub mod ast;

use plank_lexer::Token;
use bumpalo::Bump;
use crate::ast::*;

pub struct Parser<'a> {
    tokens: &'a [Token<'a>],
    pos: usize,
    arena: &'a Bump,
}

impl<'a> Parser<'a> {
    pub fn new(tokens: &'a [Token<'a>], arena: &'a Bump) -> Self {
        Self { tokens, pos: 0, arena }
    }

    pub fn parse_contract(&mut self) -> Result<Contract<'a>, String> {
        let mut constants = Vec::new();
        let mut functions = Vec::new();

        while self.pos < self.tokens.len() && self.tokens[self.pos] != Token::EOF {
            match self.tokens[self.pos] {
                Token::Const => {
                    constants.push(self.parse_stmt()?);
                }
                Token::Fn => {
                    functions.push(self.parse_function()?);
                }
                _ => {
                    return Err(format!("Unexpected token at top level: {:?}", self.tokens[self.pos]));
                }
            }
        }

        Ok(Contract {
            name: "Default",
            constants,
            functions,
            storage_layout: StorageLayout {},
        })
    }

    fn parse_function(&mut self) -> Result<Function<'a>, String> {
        self.expect(Token::Fn)?;
        let name = if let Token::Identifier(id) = self.tokens[self.pos] {
            self.pos += 1;
            id
        } else {
            return Err("Expected function name".to_string());
        };

        self.expect(Token::LParen)?;
        let mut params = Vec::new();
        while self.tokens[self.pos] != Token::RParen {
            let p_name = if let Token::Identifier(id) = self.tokens[self.pos] {
                self.pos += 1;
                id
            } else {
                return Err("Expected parameter name".to_string());
            };
            self.expect(Token::Colon)?;
            let p_ty = self.parse_type()?;
            params.push((p_name, p_ty));
            if self.tokens[self.pos] == Token::Comma {
                self.pos += 1;
            }
        }
        self.expect(Token::RParen)?;

        let ret_ty = if self.tokens[self.pos] == Token::Arrow {
            self.pos += 1;
            self.parse_type()?
        } else {
            Type::Void
        };

        let body = self.parse_block()?;

        Ok(Function {
            name,
            params,
            ret_ty,
            body,
            is_const: false,
        })
    }

    fn parse_block(&mut self) -> Result<Expr<'a>, String> {
        self.expect(Token::LBrace)?;
        let mut stmts = Vec::new();
        while self.tokens[self.pos] != Token::RBrace {
            stmts.push(self.parse_stmt()?);
        }
        self.expect(Token::RBrace)?;
        Ok(Expr::Block(stmts))
    }

    fn parse_stmt(&mut self) -> Result<Stmt<'a>, String> {
        match self.tokens[self.pos] {
            Token::Const => {
                self.pos += 1;
                let name = if let Token::Identifier(id) = self.tokens[self.pos] {
                    self.pos += 1;
                    id
                } else {
                    return Err("Expected constant name".to_string());
                };
                self.expect(Token::Colon)?;
                let ty = self.parse_type()?;
                self.expect(Token::Assign)?;
                let expr = self.parse_expr()?;
                self.expect(Token::Semicolon)?;
                Ok(Stmt::ConstDecl(name, ty, expr))
            }
            Token::U256 | Token::Bytes32 | Token::Bool | Token::Void | Token::Identifier(_) => {
                let current_token = self.tokens[self.pos];
                if let Token::Identifier(id) = current_token {
                    if id == "let" {
                        self.pos += 1;
                        let name = if let Token::Identifier(id) = self.tokens[self.pos] {
                            self.pos += 1;
                            id
                        } else {
                            return Err("Expected variable name after let".to_string());
                        };
                        self.expect(Token::Assign)?;
                        let expr = self.parse_expr()?;
                        self.expect(Token::Semicolon)?;
                        return Ok(Stmt::VarDecl(name, Type::Void, expr));
                    }
                }

                if matches!(current_token, Token::U256 | Token::Bytes32 | Token::Bool | Token::Void) {
                    let ty = self.parse_type()?;
                    let name = if let Token::Identifier(id) = self.tokens[self.pos] {
                        self.pos += 1;
                        id
                    } else {
                        return Err("Expected variable name".to_string());
                    };
                    self.expect(Token::Assign)?;
                    let expr = self.parse_expr()?;
                    self.expect(Token::Semicolon)?;
                    Ok(Stmt::VarDecl(name, ty, expr))
                } else {
                    let expr = self.parse_expr()?;
                    if self.tokens.get(self.pos) == Some(&Token::Assign) {
                        self.pos += 1;
                        let val = self.parse_expr()?;
                        self.expect(Token::Semicolon)?;
                        Ok(Stmt::Assign(Box::new(expr), val))
                    } else {
                        self.expect(Token::Semicolon)?;
                        Ok(Stmt::Expr(expr))
                    }
                }
            }
            _ => {
                let expr = self.parse_expr()?;
                self.expect(Token::Semicolon)?;
                Ok(Stmt::Expr(expr))
            }
        }
    }

    fn parse_expr(&mut self) -> Result<Expr<'a>, String> {
        self.parse_primary()
    }

    fn parse_primary(&mut self) -> Result<Expr<'a>, String> {
        match self.tokens[self.pos] {
            Token::IntLiteral(n) => {
                self.pos += 1;
                Ok(Expr::Literal(Literal::U256(n)))
            }
            Token::Identifier(id) => {
                self.pos += 1;
                if self.tokens.get(self.pos) == Some(&Token::LParen) {
                    self.pos += 1;
                    let mut args = Vec::new();
                    while self.tokens.get(self.pos) != Some(&Token::RParen) {
                        args.push(self.parse_expr()?);
                        if self.tokens.get(self.pos) == Some(&Token::Comma) {
                            self.pos += 1;
                        }
                    }
                    self.expect(Token::RParen)?;
                    Ok(Expr::FunctionCall(Box::new(Expr::Identifier(id)), args))
                } else {
                    Ok(Expr::Identifier(id))
                }
            }
            Token::EvmSload | Token::EvmSstore | Token::EvmKeccak256 | Token::EvmEmitLog | Token::EvmAddress | Token::EvmTimestamp | Token::EvmReturn => {
                let builtin = match self.tokens[self.pos] {
                    Token::EvmSload => Builtin::Sload,
                    Token::EvmSstore => Builtin::Sstore,
                    Token::EvmKeccak256 => Builtin::Keccak256,
                    Token::EvmEmitLog => Builtin::EmitLog { topics: 0 },
                    Token::EvmAddress => Builtin::Address,
                    Token::EvmTimestamp => Builtin::Timestamp,
                    Token::EvmReturn => Builtin::Return,
                    _ => unreachable!(),
                };
                self.pos += 1;
                self.expect(Token::LParen)?;
                let mut args = Vec::new();
                while self.tokens.get(self.pos) != Some(&Token::RParen) {
                    args.push(self.parse_expr()?);
                    if self.tokens.get(self.pos) == Some(&Token::Comma) {
                        self.pos += 1;
                    }
                }
                self.expect(Token::RParen)?;
                Ok(Expr::BuiltinCall(builtin, args))
            }
            _ => Err(format!("Unexpected token in expression: {:?}", self.tokens[self.pos])),
        }
    }

    fn parse_type(&mut self) -> Result<Type, String> {
        match self.tokens[self.pos] {
            Token::Void => { self.pos += 1; Ok(Type::Void) }
            Token::Bool => { self.pos += 1; Ok(Type::Bool) }
            Token::U256 => { self.pos += 1; Ok(Type::U256) }
            Token::Bytes32 => { self.pos += 1; Ok(Type::Bytes32) }
            _ => Err(format!("Expected type, found {:?}", self.tokens[self.pos])),
        }
    }

    fn expect(&mut self, token: Token<'a>) -> Result<(), String> {
        if self.pos < self.tokens.len() && self.tokens[self.pos] == token {
            self.pos += 1;
            Ok(())
        } else {
            Err(format!("Expected {:?}, found {:?}", token, self.tokens.get(self.pos)))
        }
    }
}
