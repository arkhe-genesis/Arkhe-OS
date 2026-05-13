use crate::ast::{Expr, Type};

pub enum TypeError {
    LinearCopyViolation(String),
    LinearUseAfterMove(String),
}

pub struct TypeEnv {
    moved_vars: std::collections::HashSet<String>,
}

impl TypeEnv {
    pub fn is_moved(&self, name: &str) -> bool {
        self.moved_vars.contains(name)
    }
    pub fn mark_moved(&mut self, name: &str) {
        self.moved_vars.insert(name.to_string());
    }
}

pub fn is_fd_type(_ty: &Type) -> bool {
    true // placeholder
}

pub fn expr_consumes_value(_expr: &Expr) -> bool {
    true // placeholder
}

/// Verifies linear usage of `Fd<T>` resources.
pub fn check_linear_type(ty: &Type, expr: &Expr, env: &mut TypeEnv) -> Result<(), TypeError> {
    if is_fd_type(ty) {
        match expr {
            Expr::Copy(_) => Err(TypeError::LinearCopyViolation(
                "Fd<T> is linear and cannot be copied. Use `.dup()` to duplicate.".into(),
            )),
            Expr::Variable(name) => {
                if env.is_moved(name) {
                    Err(TypeError::LinearUseAfterMove(format!(
                        "Fd<{}> has been moved",
                        name
                    )))
                } else {
                    if expr_consumes_value(expr) {
                        env.mark_moved(name);
                    }
                    Ok(())
                }
            }
        }
    } else {
        Ok(())
    }
}
