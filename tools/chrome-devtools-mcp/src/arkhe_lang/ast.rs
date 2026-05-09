use std::collections::HashMap;

// -----------------------------------------------------------------------------
// ARKHE(N) LANG (⍉) - ABSTRACT SYNTAX TREE
// The language where Retrocausality and Phase are first-class citizens.
// -----------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq)]
pub enum ArkheType {
    Phase,          // Complex phase (ℂ)
    Space,          // Spatial coordinate (ℝ³)
    Discrete,       // Integer/Symbol (ℤ)
    Manifest,       // Observable outcome (ℝ⁴)
    Tensor,         // Graphene-TPU Tensor
    ZKProof,        // Zero-Knowledge STARK Proof
}

#[derive(Debug, Clone)]
pub enum Expr {
    Literal(f64),
    PhaseLiteral(f64, f64), // Real, Imaginary
    Identifier(String),

    // A function that executes retrocausally (future determines present)
    RetrocausalBlock {
        condition: Box<Expr>,
        body: Vec<Stmt>,
        future_context: String,
    },

    // Interferometric collapse of multiple branches
    InterferenceMax {
        branches: Vec<Expr>,
        evaluator: Box<Expr>,
    },

    // ZK-STARK generation for a specific expression
    Prove(Box<Expr>),

    // Riemann Multiverse Operations
    SheetGet,
    SheetSet(Box<Expr>),
    SheetJump(Box<Expr>, Box<Expr>), // Target, State
    SheetProbe(Box<Expr>),           // Target

    // Block #171 Physics
    ArkheVerify(Box<Expr>, Box<Expr>), // Rho, Sigma
    QnetFiber(Box<Expr>, Box<Expr>),   // Photon, Length
}

#[derive(Debug, Clone)]
pub enum Stmt {
    Let(String, ArkheType, Expr),

    // A variable that persists across timeline forks
    BranchVar(String, ArkheType, Expr),

    Assign(String, Expr),
    Expr(Expr),

    // Commits a timeline, pruning divergent branches in FractalDB
    Commit(Expr),
}

#[derive(Debug, Clone)]
pub struct Function {
    pub name: String,
    pub is_retro: bool,
    pub params: Vec<(String, ArkheType)>,
    pub return_type: ArkheType,
    pub body: Vec<Stmt>,
}

#[derive(Debug, Clone)]
pub struct Program {
    pub functions: Vec<Function>,
}
