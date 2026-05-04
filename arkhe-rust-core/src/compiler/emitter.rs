use super::parser::{Stmt, Expr};

pub struct EvmEmitter {
    ast: Vec<Stmt>,
}

impl EvmEmitter {
    pub fn new(ast: Vec<Stmt>) -> Self {
        Self { ast }
    }

    pub fn emit(&self) -> Result<Vec<u8>, String> {
        let mut bytecode = Vec::new();
        for stmt in &self.ast {
            self.emit_stmt(stmt, &mut bytecode)?;
        }
        Ok(bytecode)
    }

    fn emit_stmt(&self, stmt: &Stmt, bytecode: &mut Vec<u8>) -> Result<(), String> {
        match stmt {
            Stmt::ConstDecl(_name, expr) => {
                self.emit_expr(expr, bytecode)?;
                // Simple placeholder: push to stack
            },
            Stmt::FunctionDecl(_name, _params, _ret, body) => {
                for s in body {
                    self.emit_stmt(s, bytecode)?;
                }
            },
            _ => {}
        }
        Ok(())
    }

    fn emit_expr(&self, expr: &Expr, bytecode: &mut Vec<u8>) -> Result<(), String> {
        match expr {
            Expr::Number(n) => {
                // PUSH32 (or similar)
                bytecode.push(0x7f);
                let bytes = n.to_be_bytes();
                let mut full_bytes = [0u8; 32];
                full_bytes[24..32].copy_from_slice(&bytes);
                bytecode.extend_from_slice(&full_bytes);
            },
            Expr::BuiltinCall(name, args) => {
                for arg in args {
                    self.emit_expr(arg, bytecode)?;
                }
                match name.as_str() {
                    "evm_sstore" => bytecode.push(0x55),
                    "evm_sload" => bytecode.push(0x54),
                    _ => {}
                }
            },
            _ => {}
        }
        Ok(())
    }
}
