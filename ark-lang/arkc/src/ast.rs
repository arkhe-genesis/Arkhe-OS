pub enum Expr {
    Copy(Box<Expr>),
    Variable(String),
}

pub enum Type {
    Fd(String),
}
