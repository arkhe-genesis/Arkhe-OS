// ============================================================================
// ARKHE P³ — Universal Abstract Syntax Tree (UAST)
// ============================================================================
// Representação intermediária universal que captura a semântica de qualquer
// linguagem de programação de forma canônica.
//
// Design principles:
//   1. Minimalidade: apenas conceitos que existem em TODAS as linguagens
//   2. Reversibilidade: qualquer UAST pode ser convertido para a linguagem original
//   3. Comparabilidade: dois UASTs equivalentes devem ser comparáveis
//   4. Temporalidade: cada nó tem timestamp e hash
//
// A UAST é o "lingua franca" da Catedral — o idioma que todas as linguagens falam.
// ============================================================================

use std::collections::{HashMap, BTreeMap};
use ahash::RandomState;
use serde::{Serialize, Deserialize};

// ============================================================================
// ESTRUTURA DO UAST
// ============================================================================

/// A UAST é uma árvore de nós tipados que representam conceitos universais
/// da computação, independentes de qualquer linguagem específica.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "wasm", wasm_bindgen)]
pub struct UAST {
    pub root: NodeId,
    pub nodes: HashMap<NodeId, UASTNode, RandomState>,
    pub edges: Vec<Edge>,
    pub metadata: UASTMetadata,
    pub source_info: SourceInfo,
    pub version_hash: Vec<u8>, // SHA3-256 do AST
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct UASTMetadata {
    pub language: String,
    pub dialect: Option<String>,
    pub version: String,
    pub hash_algorithm: String,
    pub timestamp_ns: u64,
    pub author: Option<String>,
    pub checksum: Vec<u8>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct SourceInfo {
    pub filename: Option<String>,
    pub source_text: Option<String>, // Opcional para economizar memória
    pub line_starts: Vec<usize>,     // Offset de início de cada linha
    pub encoding: String,
}

// ============================================================================
// NÓS DA UAST
// ============================================================================

/// Identificador único de nó na UAST
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "wasm", wasm_bindgen)]
pub struct NodeId(u64);

impl NodeId {
    pub fn new(id: u64) -> Self { Self(id) }
    pub fn to_u64(&self) -> u64 { self.0 }
}

/// Nó da UAST — representa qualquer constructo computacional
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "wasm", wasm_bindgen)]
pub struct UASTNode {
    pub id: NodeId,
    pub kind: NodeKind,
    pub children: Vec<NodeId>,
    pub attributes: HashMap<String, AttributeValue, RandomState>,
    pub source_range: SourceRange,
    pub semantic_info: Option<SemanticInfo>,
    pub temporal_info: Option<TemporalNodeInfo>,
    pub hash: Vec<u8>, // Hash do nó (para integridade)
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct SourceRange {
    pub start_line: u32,
    pub start_column: u32,
    pub end_line: u32,
    pub end_column: u32,
    pub start_offset: usize,
    pub end_offset: usize,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct SemanticInfo {
    pub type_info: Option<TypeRef>,
    pub scope_id: Option<ScopeId>,
    pub mutability: Mutability,
    pub visibility: Visibility,
    pub is_terminator: bool,         // Termina execução (return, throw)
    pub is_generator: bool,          // Produ valores (yield, async)
    pub is_pure: bool,               // Sem efeitos colaterais
    pub depends_on: Vec<NodeId>,     // Dependências de dados
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct TemporalNodeInfo {
    pub created_version: u64,        // Versão temporal do código
    pub last_modified: u64,          // Timestamp da última modificação
    pub author: Option<Vec<u8>>,     // Hash da identidade do autor
    pub lineage: Vec<NodeId>,        // Ancestrais no grafo temporal
    pub is_deleted: bool,            // Soft delete (para diffs temporais)
}

/// Aresta do grafo UAST
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Edge {
    pub source: NodeId,
    pub target: NodeId,
    pub edge_type: EdgeType,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EdgeType {
    ParentChild,     // Relação hierárquica (AST padrão)
    ControlFlow,     // Fluxo de controle
    DataFlow,        // Fluxo de dados (dependência)
    CallGraph,       // Chamada de função
    Reference,       // Referência (ex: uso de variável)
    TypeRelation,    // Relação de tipo (herança, implementação)
    ScopeLink,       // Ligação de escopo
    TemporalLink,    // Ligação temporal (versão anterior)
}

// ============================================================================
// TIPOS DE NÓ UNIVERSAIS
// ============================================================================

/// Enumeração canônica de todos os tipos de nó possíveis
/// Cada tipo representa um conceito computacional universal
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "wasm", wasm_bindgen)]
pub enum NodeKind {
    // ===== Estrutura do Programa =====
    Program,                        // Programa completo
    Module,                         // Módulo/namespaced
    Package,                        // Pacote (Java, Go, Rust)
    File,                           // Arquivo fonte
    Block,                          // Bloco delimitado { } ou indentação

    // ===== Declarações =====
    DeclVariable,                   // let, var, const, mut
    DeclFunction,                   // fn, def, function
    DeclClass,                      // class, struct
    DeclInterface,                  // interface, trait, protocol
    DeclEnum,                       // enum
    DeclEnumVariant,                // Variante de enum
    DeclUnion,                      // union (C/Rust)
    DeclTypeAlias,                  // type, typedef, typealias
    DeclImport,                     // import, use, require
    DeclExport,                     // export, pub
    DeclMacro,                      // macro_rules!, #define

    // ===== Tipos =====
    TypePrimitive,                  // i32, f64, bool, string
    TypeReference,                  // &T, *T, ref T
    TypeArray,                      // [T; N], T[]
    TypeSlice,                      // &[T], []T
    TypeTuple,                      // (T1, T2, T3)
    TypeStruct,                     // { name: T }
    TypeEnum,                       // enum type
    TypeFunction,                   // fn(T1, T2) -> T3
    TypeGeneric,                    // T, <T>
    TypeConstraint,                 // where T: Trait
    TypeUnion,                      // T1 | T2 (discriminated union)
    TypeIntersection,               // T1 & T2
    TypeOptional,                   // T?, Option<T>
    TypeNullable,                   // T | null
    TypeNever,                      // never, ! (Rust diverging)
    TypeVoid,                       // void, unit
    TypeAny,                        // any, interface{}
    TypeDynamic,                    // dynamic, var
    TypeSelf,                       // Self, self type
    TypeThis,                       // this type

    // ===== Expressões =====
    ExprLiteral,                    // Literal (int, float, string, bool, null)
    ExprIdentifier,                 // Identifier reference
    ExprUnary,                      // Unary: !x, -x, ~x, &x, *x
    ExprBinary,                     // Binary: a + b, a * b
    ExprTernary,                    // Ternary: a ? b : c
    ExprCall,                       // Function call: f(a, b)
    ExprMethodCall,                 // Method call: obj.method()
    ExprIndex,                      // Index: arr[i], map[key]
    ExprField,                      // Field access: obj.field
    ExprSpread,                     // Spread: ...arr
    ExprRest,                       // Rest: ...args
    ExprArrow,                      // Arrow function: (x) => x + 1
    ExprClosure,                    // Closure: |x| x + 1
    ExprLambda,                     // Lambda: λx.x
    ExprAwait,                      // Await: await expr
    ExprAsync,                      // Async: async { ... }
    ExprYield,                      // Yield: yield expr
    ExprReturn,                     // Return: return expr
    ExprThrow,                      // Throw: throw expr
    ExprNew,                        // New: new Class(args)
    ExprDelete,                     // Delete: delete obj.prop
    ExprTypeOf,                     // TypeOf: typeof expr
    ExprInstanceOf,                 // InstanceOf: expr instanceof Type
    ExprCast,                       // Cast: expr as Type, (Type)expr
    ExprCoalesce,                   // Coalesce: a ?? b
    ExprOptionalChain,              // Optional chain: a?.b?.c
    ExprTemplate,                   // Template literal: `hello ${name}`
    ExprAssignment,                 // Assignment: a = b
    ExprCompoundAssign,             // Compound: a += b, a <<= b
    ExprSequence,                   // Sequence: (a, b, c)
    ExprMatch,                      // Match/pattern match

    // ===== Padrões (Patterns) =====
    PatternLiteral,                 // Pattern literal
    PatternIdentifier,              // Pattern binding
    PatternWildcard,                // Wildcard: _
    PatternDestructure,             // Destructuring: { a, b }
    PatternSlice,                   // Slice pattern
    PatternRange,                   // Range pattern: 1..10
    PatternOr,                      // Alternative: a | b
    PatternGuard,                   // Guard: pattern if condition

    // ===== Instruções/Statements =====
    StmtExpression,                 // Expression statement
    StmtBlock,                      // Block statement
    StmtIf,                         // If-else
    StmtWhile,                      // While loop
    StmtFor,                        // For loop
    StmtForIn,                      // For-in loop
    StmtForOf,                      // For-of loop
    StmtDoWhile,                    // Do-while loop
    StmtSwitch,                     // Switch/case
    StmtCase,                       // Case branch
    StmtDefault,                   // Default case
    StmtBreak,                      // Break
    StmtContinue,                   // Continue
    StmtReturn,                     // Return
    StmtThrow,                      // Throw
    StmtTry,                        // Try-catch
    StmtCatch,                      // Catch block
    StmtFinally,                    // Finally block
    StmtWith,                       // With statement
    StmtLabeled,                    // Labeled statement
    StmtGoto,                       // Goto (rare but exists in C)
    StmtSuspend,                    // Suspend (coroutines)
    StmtResume,                     // Resume (coroutines)

    // ===== Controle de Concorrência =====
    ConcurrentSpawn,                // spawn, goroutine
    ConcurrentSend,                 // Channel send: ch <- val
    ConcurrentReceive,              // Channel receive: <-ch
    ConcurrentSelect,               // select
    ConcurrentLock,                 // lock/mutex
    ConcurrentAtomic,               // atomic operation

    // ===== Orientação a Objetos =====
    OOPClass,                       // Class declaration
    OOPInterface,                   // Interface/trait
    OOPField,                       // Class field/property
    OOPMethod,                      // Class method
    OOPConstructor,                 // Constructor
    OOPSuper,                       // super/base
    OOPThis,                        // this/self
    OOPInherit,                     // Inheritance
    OOPImplement,                   // Implementation
    OOPAccessModifier,              // public/private/protected

    // ===== Prolog / Lógico =====
    LogicFact,                      // Fact in Prolog
    LogicRule,                      // Rule in Prolog
    LogicQuery,                     // Query in Prolog
    LogicPredicate,                 // Predicate
    LogicUnification,               // Unification
    LogicCut,                       // Cut (!)

    // ===== SQL =====
    SQLSelect,                      // SELECT
    SQLFrom,                        // FROM
    SQLJoin,                        // JOIN
    SQLWhere,                       // WHERE
    SQLGroupBy,                     // GROUP BY
    SQLOrderBy,                     // ORDER BY
    SQLLimit,                       // LIMIT
    SQLInsert,                      // INSERT
    SQLUpdate,                      // UPDATE
    SQLDelete,                      // DELETE
    SQLCreate,                      // CREATE TABLE
    SQLAlter,                       // ALTER TABLE
    SQLDrop,                        // DROP
    SQLUnion,                       // UNION

    // ===== Graph Query =====
    GraphMatch,                     // MATCH (Cypher)
    GraphCreate,                    // CREATE (Cypher)
    GraphWhere,                     // WHERE in graph context
    GraphRelation,                  // Relationship
    GraphProperty,                  // Property on node/edge

    // ===== Blockchain/Smart Contract =====
    ChainStorage,                   // storage (Solidity/Cairo)
    ChainMapping,                   // mapping
    ChainEvent,                     // event
    ChainModifier,                  // modifier
    ChainConstructor,               // constructor
    ChainPayable,                   // payable
    ChainView,                      // view/pure
    ChainExternal,                  // external
    ChainIndexed,                   // indexed

    // ===== Wasm Specific =====
    WasmModule,                     // (module)
    WasmFunction,                   // (func)
    WasmParam,                      // (param)
    WasmResult,                     // (result)
    WasmLocal,                      // (local)
    WasmGlobal,                     // (global)
    WasmMemory,                     // (memory)
    WasmTable,                      // (table)
    WasmData,                       // (data)
    WasmElem,                       // (elem)

    // ===== Annotations/Attributes =====
    Annotation,                     // @Decorator, #[], #[cfg(...)]
    Attribute,                      // Attribute: #[attribute]
    Directive,                      // #pragma, #include

    // ===== Assembly =====
    AsmInstruction,                 // Assembly instruction
    AsmRegister,                    // Register reference
    AsmLabel,                       // Label
    AsmDirective,                   // Directive (.text, .data, etc.)

    // ===== Misc =====
    DocComment,                     /// Documentation comment
    Comment,                        // Comment
    Meta,                           // Meta information
    Placeholder,                    // Placeholder for incomplete parsing
}

/// Valor de atributo
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "wasm", wasm_bindgen)]
pub enum AttributeValue {
    String(String),
    Integer(i64),
    Float(f64),
    Boolean(bool),
    List(Vec<AttributeValue>),
    Map(HashMap<String, AttributeValue, RandomState>),
    NodeRef(NodeId),
    Bytes(Vec<u8>),
    None,
}

/// Referência de tipo
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct TypeRef {
    pub name: String,
    pub generics: Vec<TypeRef>,
    pub nullable: bool,
    pub reference: bool,
    pub mutable: bool,
}

/// Escopo
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ScopeId(String);

/// Mutabilidade
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Mutability {
    Immutable,
    Mutable,
    Const,
}

/// Visibilidade
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Visibility {
    Public,
    Private,
    Protected,
    Internal,
    Crate,      // Rust
    Package,    // Go, Java
}

// ============================================================================
// OPERAÇÕES DA UAST
// ============================================================================

impl UAST {
    /// Cria nova UAST vazia
    pub fn new(language: &str) -> Self {
        Self {
            root: NodeId(0),
            nodes: HashMap::default(),
            edges: Vec::new(),
            metadata: UASTMetadata {
                language: language.to_string(),
                dialect: None,
                version: String::new(),
                hash_algorithm: "sha3-256".to_string(),
                timestamp_ns: 0,
                author: None,
                checksum: Vec::new(),
            },
            source_info: SourceInfo {
                filename: None,
                source_text: None,
                line_starts: Vec::new(),
                encoding: "utf-8".to_string(),
            },
            version_hash: Vec::new(),
        }
    }

    /// Adiciona nó à UAST
    pub fn add_node(&mut self, kind: NodeKind, source_range: SourceRange) -> NodeId {
        let id = self.generate_id();
        let node = UASTNode {
            id,
            kind,
            children: Vec::new(),
            attributes: HashMap::default(),
            source_range,
            semantic_info: None,
            temporal_info: None,
            hash: Vec::new(),
        };
        self.nodes.insert(id, node);
        id
    }

    /// Adiciona aresta entre nós
    pub fn add_edge(&mut self, source: NodeId, target: NodeId, edge_type: EdgeType) {
        self.edges.push(Edge { source, target, edge_type });
    }

    /// Computa hash da UAST para integridade
    pub fn compute_hash(&self) -> Vec<u8> {
        let serialized = serde_json::to_vec(&self.nodes).unwrap_or_default();
        use sha3::Digest;
        sha3::Sha3_256::digest(&serialized).to_vec()
    }

    /// Gera próximo NodeId
    fn generate_id(&self) -> NodeId {
        NodeId(self.nodes.len() as u64 + 1)
    }

    /// Total de nós
    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    /// Profundidade máxima da árvore
    pub fn max_depth(&self) -> usize {
        self.depth_from(self.root, 0)
    }

    fn depth_from(&self, node_id: NodeId, current_depth: usize) -> usize {
        let node = match self.nodes.get(&node_id) {
            Some(n) => n,
            None => return current_depth,
        };
        let mut max = current_depth;
        for &child_id in &node.children {
            let d = self.depth_from(child_id, current_depth + 1);
            if d > max { max = d; }
        }
        max
    }
}
