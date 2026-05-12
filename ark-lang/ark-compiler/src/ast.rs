#[derive(Debug, PartialEq, Clone)]
pub enum Type {
    Int,
    Float,
    Bool,
    String,
    Byte,
    Unit,
    Custom(String),
    Generic(String, Vec<Type>),
}

#[derive(Debug, PartialEq, Clone)]
pub enum Expr {
    IntLit(String),
    FloatLit(String),
    BoolLit(bool),
    StringLit(String),
    ByteLit(String),
    Ident(String),
    FieldAccess(Box<Expr>, String),
    MethodCall(Box<Expr>, String, Vec<Expr>),
    FnCall(Box<Expr>, Vec<Expr>),
    BinaryOp(Box<Expr>, String, Box<Expr>),
    MacroCall(String, Vec<Expr>), // macro(exprs...)
    If(Box<Expr>, Box<Block>, Option<Box<Expr>>), // Condition, Then, Else (Optionally another if or block)
    Match(Box<Expr>, Vec<(Pattern, Expr)>),
    Block(Box<Block>),
    Return(Option<Box<Expr>>),
    Tuple(Vec<Expr>),
    Path(Vec<String>), // a::b::c
}

#[derive(Debug, PartialEq, Clone)]
pub enum Pattern {
    Ident(String),
    EnumTuple(String, Vec<Pattern>),
    Wildcard,
}

#[derive(Debug, PartialEq, Clone)]
pub enum Stmt {
    Let {
        name: String,
        ty: Option<Type>,
        init: Option<Expr>,
        is_mut: bool,
    },
    Assign(Expr, Expr),
    Expr(Expr),
    For(String, Expr, Block),
    Loop(Block),
}

#[derive(Debug, PartialEq, Clone)]
pub struct Block {
    pub stmts: Vec<Stmt>,
}

#[derive(Debug, PartialEq, Clone)]
pub enum Item {
    Fn {
        name: String,
        params: Vec<(String, Type)>,
        ret_ty: Option<Type>,
        body: Block,
    },
    Struct {
        name: String,
        fields: Vec<(String, Type)>,
        is_linear: bool,
    },
    Enum {
        name: String,
        variants: Vec<(String, Vec<Type>)>,
    },
    Trait {
        name: String,
        methods: Vec<TraitMethod>,
    },
    Impl {
        trait_name: Option<String>,
        target: Type,
        methods: Vec<Item>, // Item::Fn
    },
    BlockDef {
        name: String,
        body: Block,
    },
    Use(Vec<String>),
}

#[derive(Debug, PartialEq, Clone)]
pub struct TraitMethod {
    pub name: String,
    pub params: Vec<(String, Type)>,
    pub ret_ty: Option<Type>,
}

#[derive(Debug, PartialEq, Clone)]
pub struct Ast {
    pub items: Vec<Item>,
}
