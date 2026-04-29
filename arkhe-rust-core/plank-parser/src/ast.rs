pub enum Type {
    Void,
    Bool,
    U256,
    I256,
    Bytes32,
    Address,
    Array(Box<Type>, usize),
    Tuple(Vec<Type>),
    Function(Vec<Type>, Box<Type>), // params, retorno
}

pub enum Literal {
    U256(ethnum::u256),
    Bool(bool),
    Bytes32([u8; 32]),
    String(String),
}

#[derive(Debug)]
pub enum Builtin {
    Sload,
    Sstore,
    Keccak256,
    EmitLog { topics: u8 },
    Address,
    Timestamp,
    Return,
}

pub enum BinOp {
    Add, Sub, Mul, Div,
    Eq, Ne, Lt, Gt, Le, Ge,
}

pub enum UnOp {
    Not, Neg,
}

pub enum Expr<'a> {
    Literal(Literal),
    Identifier(&'a str),
    BuiltinCall(Builtin, Vec<Expr<'a>>),
    FunctionCall(Box<Expr<'a>>, Vec<Expr<'a>>),
    BinaryOp(BinOp, Box<Expr<'a>>, Box<Expr<'a>>),
    UnaryOp(UnOp, Box<Expr<'a>>),
    IfElse(Box<Expr<'a>>, Box<Expr<'a>>, Option<Box<Expr<'a>>>),
    Block(Vec<Stmt<'a>>),
}

pub enum Stmt<'a> {
    ConstDecl(&'a str, Type, Expr<'a>),
    VarDecl(&'a str, Type, Expr<'a>),
    Assign(Box<Expr<'a>>, Expr<'a>),
    Expr(Expr<'a>),
    Return(Expr<'a>),
}

pub struct Function<'a> {
    pub name: &'a str,
    pub params: Vec<(&'a str, Type)>,
    pub ret_ty: Type,
    pub body: Expr<'a>,
    pub is_const: bool, // fn const = comptime
}

pub struct StorageLayout {}

pub struct Contract<'a> {
    pub name: &'a str,
    pub constants: Vec<Stmt<'a>>,
    pub functions: Vec<Function<'a>>,
    pub storage_layout: StorageLayout,
}
