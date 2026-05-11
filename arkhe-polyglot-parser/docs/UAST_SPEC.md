# UAST Specification (Universal Abstract Syntax Tree)

## 1. Philosophy

A UAST captures the **meaning** of code, not its syntax. Two programs
in different languages that do the same thing should produce equivalent
UASTs (modulo language-specific idioms).

## 2. Node Categories

### 2.1 Structural Nodes
| Kind | Description | Example |
|------|-------------|---------|
| `Program` | Root of the AST | Entire source file |
| `Module` | Namespaced unit | Python module, Rust mod |
| `Block` | Delimited statement group | `{ ... }` or indented block |

### 2.2 Declaration Nodes
| Kind | Description | Example |
|------|-------------|---------|
| `DeclVariable` | Variable declaration | `let x = 42` |
| `DeclFunction` | Function/method definition | `fn foo(a: i32) -> i32` |
| `DeclClass` | Class/struct definition | `class Foo { ... }` |
| `DeclInterface` | Interface/trait | `trait Bar { ... }` |
| `DeclEnum` | Enumeration | `enum Color { Red, Green, Blue }` |
| `DeclImport` | Import statement | `import os` |
| `DeclExport` | Export statement | `pub fn ...` |
| `DeclTypeAlias` | Type alias | `type MyInt = i32` |

### 2.3 Expression Nodes
| Kind | Description |
|------|-------------|
| `ExprLiteral` | `42`, `"hello"`, `true`, `null` |
| `ExprIdentifier` | Variable/function reference |
| `ExprUnary` | `!x`, `-x`, `&x`, `*x` |
| `ExprBinary` | `a + b`, `x && y`, `a == b` |
| `ExprTernary` | `a ? b : c` |
| `ExprCall` | `f(a, b)`, `obj.method()` |
| `ExprArrow` | `(x) => x + 1` |
| `ExprAwait` | `await promise` |
| `ExprReturn` | `return value` |
| `ExprThrow` | `throw error` |
| `ExprCast` | `x as T`, `(T)x` |
| `ExprTemplate` | `` `Hello ${name}` `` |
| `ExprMatch` | Pattern matching expressions |

### 2.4 Statement Nodes
| Kind | Description |
|------|-------------|
| `StmtExpression` | Expression as statement |
| `StmtIf` | If-else branching |
| `StmtWhile` | While loop |
| `StmtFor` | For loop (C-style) |
| `StmtForIn` | For-in loop |
| `StmtSwitch` | Switch/case |
| `StmtBreak/Continue` | Loop control |
| `StmtTry` | Try-catch-finally |
| `StmtLabeled` | Labeled statement |

### 2.5 Type Nodes
| Kind | Description |
|------|-------------|
| `TypePrimitive` | `i32`, `f64`, `bool`, `string` |
| `TypeReference` | `&T`, `*T` |
| `TypeArray` | `[T; N]`, `T[]` |
| `TypeTuple` | `(T1, T2, T3)` |
| `TypeStruct` | `{ name: T }` |
| `TypeEnum` | Custom enum type |
| `TypeFunction` | `fn(A, B) -> C` |
| `TypeGeneric` | `T`, `<T>` |
| `TypeOptional` | `Option<T>`, `T?` |
| `TypeUnion` | `A | B` |

### 2.6 OOP Nodes
| Kind | Description |
|------|-------------|
| `OOPField` | Class field/property |
| `OOPMethod` | Class method |
| `OOPConstructor` | Object constructor |
| `OOPInherit` | Inheritance relationship |

### 2.7 Concurrency Nodes
| Kind | Description |
|------|-------------|
| `ConcurrentSpawn` | `spawn`, `goroutine` |
| `ConcurrentSend` | Channel send `<-` |
| `ConcurrentReceive` | Channel receive |

### 2.8 Domain-Specific Nodes
| Kind | Description |
|------|-------------|
| `SQLSelect` | SQL SELECT query |
| `GraphMatch` | Cypher MATCH pattern |
| `ChainStorage` | Smart contract storage |
| `WasmModule` | WebAssembly module |
| `Annotation` | @Decorator, #[attribute] |

## 3. Semantic Information

Each UAST node can carry semantic information:

```rust
SemanticInfo {
    type_info: Option<TypeRef>,      // Resolved type
    scope_id: Option<ScopeId>,       // Containing scope
    mutability: Mutability,          // Immutable/Mutable/Const
    visibility: Visibility,          // Public/Private/Protected
    is_terminator: bool,             // Terminates execution
    is_generator: bool,              // Produces values lazily
    is_pure: bool,                   // No side effects
    depends_on: Vec<NodeId>,         // Data dependencies
}
```

## 4. Temporal Information

For ARKHE temporal tracking:

```rust
TemporalNodeInfo {
    created_version: u64,            // Version number
    last_modified: u64,              // Last change timestamp
    author: Option<Vec<u8>>,         // Author identity hash
    lineage: Vec<NodeId>,            // Ancestors in time
    is_deleted: bool,                // Soft delete flag
}
```

## 5. Equivalence

Two UASTs are **semantically equivalent** if:
1. Same structural shape (modulo variable naming)
2. Same semantic information on corresponding nodes
3. Same type relationships
4. Same control flow graph structure
