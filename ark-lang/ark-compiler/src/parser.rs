use crate::ast::{Ast, Block, Expr, Item, Stmt, TraitMethod, Type};
use crate::lexer::Token;

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Result<Token, ()>>) -> Self {
        let valid_tokens = tokens.into_iter().filter_map(|t| t.ok()).collect();
        Self {
            tokens: valid_tokens,
            pos: 0,
        }
    }

    fn peek(&self) -> Option<&Token> {
        self.tokens.get(self.pos)
    }

    fn advance(&mut self) -> Option<&Token> {
        let t = self.tokens.get(self.pos);
        self.pos += 1;
        t
    }

    fn expect(&mut self, expected: Token) -> Result<(), String> {
        if let Some(t) = self.peek() {
            if *t == expected {
                self.advance();
                Ok(())
            } else {
                Err(format!("Expected {:?}, found {:?}", expected, t))
            }
        } else {
            Err(format!("Expected {:?}, found EOF", expected))
        }
    }

    pub fn parse(&mut self) -> Result<Ast, String> {
        let mut items = Vec::new();
        while self.peek().is_some() {
            items.push(self.parse_item()?);
        }
        Ok(Ast { items })
    }

    fn parse_item(&mut self) -> Result<Item, String> {
        match self.peek() {
            Some(Token::Fn) => self.parse_fn(),
            Some(Token::Struct) => self.parse_struct(false),
            Some(Token::Hash) => {
                // Check for #[linear]
                self.advance();
                self.expect(Token::LBracket)?;
                self.expect(Token::LinearKw)?;
                self.expect(Token::RBracket)?;
                if let Some(Token::Struct) = self.peek() {
                    self.parse_struct(true)
                } else if let Some(Token::Type) = self.peek() {
                    // For #[linear] type Fd<T, P> { ... }
                    self.advance();
                    let name = self.parse_ident()?;
                    // Skip generics for now
                    if self.peek() == Some(&Token::Less) {
                        self.parse_generics()?;
                    }
                    let block = self.parse_block()?;
                    Ok(Item::BlockDef { name, body: block }) // Hack: reusing BlockDef to represent this
                } else {
                    Err("Expected struct or type after #[linear]".to_string())
                }
            }
            Some(Token::Enum) => self.parse_enum(),
            Some(Token::Trait) => self.parse_trait(),
            Some(Token::Impl) => self.parse_impl(),
            Some(Token::Block) => {
                self.advance(); // consume 'block'
                let name = self.parse_ident()?;
                let body = self.parse_block()?;
                Ok(Item::BlockDef { name, body })
            }
            Some(Token::Use) => {
                self.advance();
                let mut path = Vec::new();
                path.push(self.parse_ident()?);
                while self.peek() == Some(&Token::ColonColon) {
                    self.advance();
                    path.push(self.parse_ident()?);
                }
                self.expect(Token::Semi)?;
                Ok(Item::Use(path))
            }
            _ => Err(format!("Unexpected token at top level: {:?}", self.peek())),
        }
    }

    fn parse_fn(&mut self) -> Result<Item, String> {
        self.advance(); // consume 'fn'
        let name = self.parse_ident()?;
        self.expect(Token::LParen)?;
        let mut params = Vec::new();
        while self.peek() != Some(&Token::RParen) {
            let p_name = self.parse_ident()?;
            self.expect(Token::Colon)?;
            let p_type = self.parse_type()?;
            params.push((p_name, p_type));
            if self.peek() == Some(&Token::Comma) {
                self.advance();
            } else {
                break;
            }
        }
        self.expect(Token::RParen)?;

        let mut ret_ty = None;
        if self.peek() == Some(&Token::Arrow) {
            self.advance();
            ret_ty = Some(self.parse_type()?);
        }

        let body = self.parse_block()?;

        Ok(Item::Fn {
            name,
            params,
            ret_ty,
            body,
        })
    }

    fn parse_struct(&mut self, is_linear: bool) -> Result<Item, String> {
        self.advance(); // consume 'struct'
        let name = self.parse_ident()?;
        self.expect(Token::LBrace)?;
        let mut fields = Vec::new();
        while self.peek() != Some(&Token::RBrace) {
            let f_name = self.parse_ident()?;
            self.expect(Token::Colon)?;
            let f_type = self.parse_type()?;
            fields.push((f_name, f_type));
            if self.peek() == Some(&Token::Comma) {
                self.advance();
            } else {
                break;
            }
        }
        self.expect(Token::RBrace)?;

        Ok(Item::Struct {
            name,
            fields,
            is_linear,
        })
    }

    fn parse_enum(&mut self) -> Result<Item, String> {
        self.advance();
        let name = self.parse_ident()?;
        if self.peek() == Some(&Token::Less) {
             self.parse_generics()?;
        }
        self.expect(Token::LBrace)?;
        let mut variants = Vec::new();
        while self.peek() != Some(&Token::RBrace) {
            let v_name = self.parse_ident()?;
            let mut v_types = Vec::new();
            if self.peek() == Some(&Token::LParen) {
                self.advance();
                while self.peek() != Some(&Token::RParen) {
                    v_types.push(self.parse_type()?);
                    if self.peek() == Some(&Token::Comma) {
                        self.advance();
                    } else {
                        break;
                    }
                }
                self.expect(Token::RParen)?;
            }
            variants.push((v_name, v_types));
            if self.peek() == Some(&Token::Comma) {
                self.advance();
            } else {
                break;
            }
        }
        self.expect(Token::RBrace)?;
        Ok(Item::Enum { name, variants })
    }

    fn parse_trait(&mut self) -> Result<Item, String> {
        self.advance();
        let name = self.parse_ident()?;
        self.expect(Token::LBrace)?;
        let mut methods = Vec::new();
        while self.peek() != Some(&Token::RBrace) {
            self.expect(Token::Fn)?;
            let m_name = self.parse_ident()?;
            self.expect(Token::LParen)?;
            let mut params = Vec::new();
            if self.peek() == Some(&Token::SelfKw) {
                 self.advance();
                 params.push(("self".to_string(), Type::Custom("Self".to_string())));
                 if self.peek() == Some(&Token::Comma) { self.advance(); }
            }
            while self.peek() != Some(&Token::RParen) {
                let p_name = self.parse_ident()?;
                self.expect(Token::Colon)?;
                let p_type = self.parse_type()?;
                params.push((p_name, p_type));
                if self.peek() == Some(&Token::Comma) {
                    self.advance();
                } else {
                    break;
                }
            }
            self.expect(Token::RParen)?;
            let mut ret_ty = None;
            if self.peek() == Some(&Token::Arrow) {
                self.advance();
                ret_ty = Some(self.parse_type()?);
            }
            self.expect(Token::Semi)?;
            methods.push(TraitMethod { name: m_name, params, ret_ty });
        }
        self.expect(Token::RBrace)?;
        Ok(Item::Trait { name, methods })
    }

    fn parse_impl(&mut self) -> Result<Item, String> {
        self.advance();
        let trait_name = self.parse_ident()?;
        let mut t_name = Some(trait_name.clone());
        let mut target = Type::Custom(trait_name);

        if self.peek() == Some(&Token::For) {
            self.advance();
            target = self.parse_type()?;
        } else {
            t_name = None;
        }

        self.expect(Token::LBrace)?;
        let mut methods = Vec::new();
        while self.peek() != Some(&Token::RBrace) {
             methods.push(self.parse_fn()?);
        }
        self.expect(Token::RBrace)?;
        Ok(Item::Impl { trait_name: t_name, target, methods })
    }

    fn parse_generics(&mut self) -> Result<Vec<String>, String> {
         self.expect(Token::Less)?;
         let mut params = Vec::new();
         while self.peek() != Some(&Token::Greater) {
              params.push(self.parse_ident()?);
              if self.peek() == Some(&Token::Comma) {
                  self.advance();
              } else {
                  break;
              }
         }
         self.expect(Token::Greater)?;
         Ok(params)
    }

    fn parse_type(&mut self) -> Result<Type, String> {
        match self.peek() {
            Some(Token::IntType) => { self.advance(); Ok(Type::Int) },
            Some(Token::FloatType) => { self.advance(); Ok(Type::Float) },
            Some(Token::BoolType) => { self.advance(); Ok(Type::Bool) },
            Some(Token::StringType) => { self.advance(); Ok(Type::String) },
            Some(Token::ByteType) => { self.advance(); Ok(Type::Byte) },
            Some(Token::UnitType) => { self.advance(); Ok(Type::Unit) },
            Some(Token::LParen) => {
                 self.advance();
                 self.expect(Token::RParen)?;
                 Ok(Type::Unit)
            },
            Some(Token::Ident(name)) => {
                let n = name.clone();
                self.advance();
                if self.peek() == Some(&Token::Less) {
                    let mut args = Vec::new();
                    self.advance(); // consume '<'
                    while self.peek() != Some(&Token::Greater) {
                        args.push(self.parse_type()?);
                        if self.peek() == Some(&Token::Comma) {
                            self.advance();
                        } else {
                            break;
                        }
                    }
                    self.expect(Token::Greater)?;
                    Ok(Type::Generic(n, args))
                } else {
                    Ok(Type::Custom(n))
                }
            }
            _ => Err(format!("Expected type, found {:?}", self.peek())),
        }
    }

    fn parse_block(&mut self) -> Result<Block, String> {
        self.expect(Token::LBrace)?;
        let mut stmts = Vec::new();
        while self.peek() != Some(&Token::RBrace) {
            stmts.push(self.parse_stmt()?);
        }
        self.expect(Token::RBrace)?;
        Ok(Block { stmts })
    }

    fn parse_stmt(&mut self) -> Result<Stmt, String> {
        match self.peek() {
            Some(Token::Let) => {
                self.advance();
                let mut is_mut = false;
                if self.peek() == Some(&Token::Mut) {
                    is_mut = true;
                    self.advance();
                }
                let name = self.parse_ident()?;
                let mut ty = None;
                if self.peek() == Some(&Token::Colon) {
                    self.advance();
                    ty = Some(self.parse_type()?);
                }
                let mut init = None;
                if self.peek() == Some(&Token::Eq) {
                    self.advance();
                    init = Some(self.parse_expr()?);
                }
                self.expect(Token::Semi)?;
                Ok(Stmt::Let { name, ty, init, is_mut })
            }
            Some(Token::For) => {
                 self.advance();
                 let item = self.parse_ident()?;
                 self.expect(Token::In)?;
                 let expr = self.parse_expr()?;
                 let block = self.parse_block()?;
                 Ok(Stmt::For(item, expr, block))
            }
            Some(Token::Loop) => {
                 self.advance();
                 let block = self.parse_block()?;
                 Ok(Stmt::Loop(block))
            }
            _ => {
                let expr = self.parse_expr()?;
                if self.peek() == Some(&Token::Semi) {
                    self.advance();
                    Ok(Stmt::Expr(expr))
                } else {
                     // check for assignment?
                     Err(format!("Expected ; after expr, found {:?}", self.peek()))
                }
            }
        }
    }

    fn parse_expr(&mut self) -> Result<Expr, String> {
         let mut left = self.parse_primary()?;

         // Handle method calls and field access
         while self.peek() == Some(&Token::Dot) {
             self.advance();
             let name = self.parse_ident()?;
             if self.peek() == Some(&Token::LParen) {
                 self.advance();
                 let mut args = Vec::new();
                 while self.peek() != Some(&Token::RParen) {
                     args.push(self.parse_expr()?);
                     if self.peek() == Some(&Token::Comma) {
                         self.advance();
                     } else {
                         break;
                     }
                 }
                 self.expect(Token::RParen)?;
                 left = Expr::MethodCall(Box::new(left), name, args);
             } else {
                 left = Expr::FieldAccess(Box::new(left), name);
             }
         }

         while let Some(tok) = self.peek() {
             let op_str = match tok {
                 Token::EqEq => "==",
                 Token::NotEq => "!=",
                 Token::Less => "<",
                 Token::Greater => ">",
                 Token::LessEq => "<=",
                 Token::GreaterEq => ">=",
                 Token::Plus => "+",
                 Token::Minus => "-",
                 Token::Star => "*",
                 Token::Slash => "/",
                 _ => break,
             };
             let op = op_str.to_string();
             self.advance(); // consume op
             let right = self.parse_primary()?;
             left = Expr::BinaryOp(Box::new(left), op, Box::new(right));
         }

         Ok(left)
    }

    fn parse_primary(&mut self) -> Result<Expr, String> {
        match self.peek() {
            Some(Token::IntLit(s)) => {
                let val = s.clone();
                self.advance();
                Ok(Expr::IntLit(val))
            }
            Some(Token::FloatLit(s)) => {
                let val = s.clone();
                self.advance();
                Ok(Expr::FloatLit(val))
            }
            Some(Token::StringLit(s)) => {
                let val = s.clone();
                self.advance();
                Ok(Expr::StringLit(val))
            }
            Some(Token::True) => {
                self.advance();
                Ok(Expr::BoolLit(true))
            }
            Some(Token::False) => {
                self.advance();
                Ok(Expr::BoolLit(false))
            }
            Some(Token::If) => {
                 self.advance();
                 let cond = self.parse_expr()?;
                 let then_block = self.parse_block()?;
                 let mut else_expr = None;
                 if self.peek() == Some(&Token::Else) {
                     self.advance();
                     if self.peek() == Some(&Token::If) {
                          else_expr = Some(Box::new(self.parse_primary()?)); // parse `if` as expr
                     } else {
                          else_expr = Some(Box::new(Expr::Block(Box::new(self.parse_block()?))));
                     }
                 }
                 Ok(Expr::If(Box::new(cond), Box::new(then_block), else_expr))
            }
            Some(Token::Return) => {
                 self.advance();
                 if self.peek() == Some(&Token::Semi) {
                      Ok(Expr::Return(None))
                 } else {
                      let expr = self.parse_expr()?;
                      Ok(Expr::Return(Some(Box::new(expr))))
                 }
            }
            Some(Token::Prove) | Some(Token::Anchor) | Some(Token::Pay) | Some(Token::Orcid) => {
                 let name = match self.peek().unwrap() {
                     Token::Prove => "prove".to_string(),
                     Token::Anchor => "anchor".to_string(),
                     Token::Pay => "pay".to_string(),
                     Token::Orcid => "orcid".to_string(),
                     _ => unreachable!()
                 };
                 self.advance();
                 self.expect(Token::LParen)?;
                 let mut args = Vec::new();
                 while self.peek() != Some(&Token::RParen) {
                     args.push(self.parse_expr()?);
                     if self.peek() == Some(&Token::Comma) {
                         self.advance();
                     } else {
                         break;
                     }
                 }
                 self.expect(Token::RParen)?;
                 Ok(Expr::MacroCall(name, args))
            }
            Some(Token::Ident(name)) => {
                let n = name.clone();
                self.advance();

                // Path handling (e.g. a::b::c)
                let mut path = vec![n.clone()];
                while self.peek() == Some(&Token::ColonColon) {
                     self.advance();
                     path.push(self.parse_ident()?);
                }

                if self.peek() == Some(&Token::LParen) {
                    self.advance(); // consume '('
                    let mut args = Vec::new();
                    while self.peek() != Some(&Token::RParen) {
                        args.push(self.parse_expr()?);
                        if self.peek() == Some(&Token::Comma) {
                            self.advance();
                        } else {
                            break;
                        }
                    }
                    self.expect(Token::RParen)?;
                    if path.len() > 1 {
                         Ok(Expr::FnCall(Box::new(Expr::Path(path)), args))
                    } else {
                         Ok(Expr::FnCall(Box::new(Expr::Ident(n)), args))
                    }
                } else if self.peek() == Some(&Token::MACRO_CALL) {
                    // Placeholder if we add macro calls via ident!
                    Err("Not implemented macro".to_string())
                } else if path.len() > 1 {
                    Ok(Expr::Path(path))
                } else {
                    Ok(Expr::Ident(n))
                }
            }
            _ => Err(format!("Expected expression, found {:?}", self.peek())),
        }
    }

    fn parse_ident(&mut self) -> Result<String, String> {
        if let Some(Token::Ident(name)) = self.peek() {
            let n = name.clone();
            self.advance();
            Ok(n)
        } else {
            Err(format!("Expected identifier, found {:?}", self.peek()))
        }
    }
}

// Dummy match for missing macro
impl Token {
   const MACRO_CALL: Token = Token::UnitType; // Just satisfying compiler for dead code
}
