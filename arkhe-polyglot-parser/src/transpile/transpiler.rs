// ============================================================================
// ARKHE P³ — Transpiler Core
// ============================================================================
// Converte UAST para qualquer linguagem suportada.
// O processo é:
//   Source Code → Lexer → Parser → UAST → Semantic Oracle → CodeGen → Optimizer → Output
// ============================================================================

use crate::ast::{UAST, UASTNode, NodeId, NodeKind, AttributeValue};
use crate::ast::AttributeValue as AV;
use crate::ast::TypeRef;
use std::collections::{HashMap, HashSet};

/// Transpiler principal
pub struct Transpiler {
    target_language: String,
    config: TranspileConfig,
    optimizations_applied: usize,
}

#[derive(Clone, Debug)]
pub struct TranspileConfig {
    /// Nível de otimização (0-3)
    pub optimization_level: u8,
    /// Preservar comentários
    pub preserve_comments: bool,
    /// Formatar saída
    pub format_output: bool,
    /// Mapear erros para localização original
    pub map_errors: bool,
    /// Gerar source map
    pub source_map: bool,
}

impl Default for TranspileConfig {
    fn default() -> Self {
        Self {
            optimization_level: 2,
            preserve_comments: true,
            format_output: true,
            map_errors: true,
            source_map: true,
        }
    }
}

/// Código transpilado com metadados
pub struct TranspiledCode {
    pub code: String,
    pub source_map: Option<String>,
    pub line_map: Vec<(u32, u32)>, // (source_line, target_line)
    pub warnings: Vec<TranspileWarning>,
    pub metrics: TranspileMetrics,
}

#[derive(Clone, Debug)]
pub struct TranspileWarning {
    pub kind: String,
    pub message: String,
    pub source_line: u32,
}

#[derive(Clone, Debug, Default)]
pub struct TranspileMetrics {
    pub nodes_visited: usize,
    pub transformations_applied: usize,
    pub optimizations_applied: usize,
    pub output_size_bytes: usize,
}

impl Transpiler {
    /// Criar novo transpiler
    pub fn new(target_language: &str, config: TranspileConfig) -> Self {
        Self {
            target_language: target_language.to_string(),
            config,
            optimizations_applied: 0,
        }
    }

    /// Transpilar UAST para linguagem alvo
    pub fn transpile(&mut self, uast: &UAST) -> Result<TranspiledCode, TranspileError> {
        if !self.is_language_supported(&self.target_language) {
            return Err(TranspileError::UnsupportedLanguage(self.target_language.clone()));
        }

        // 1. Otimizar UAST antes da geração
        let optimized_uast = if self.config.optimization_level > 0 {
            self.optimize_uast(uast)?
        } else {
            uast.clone()
        };

        // 2. Gerar código
        let code = self.generate_code(&optimized_uast)?;

        // 3. Formatar se necessário
        let code = if self.config.format_output {
            self.format_code(&code)?
        } else {
            code
        };

        // 4. Gerar source map
        let source_map = if self.config.source_map {
            Some(self.generate_source_map(uast, &optimized_uast)?)
        } else {
            None
        };

        Ok(TranspiledCode {
            code: code.clone(),
            source_map,
            line_map: Vec::new(),
            warnings: Vec::new(),
            metrics: TranspileMetrics {
                nodes_visited: optimized_uast.node_count(),
                transformations_applied: 0,
                optimizations_applied: self.optimizations_applied,
                output_size_bytes: code.len(),
            },
        })
    }

    /// Gerar código a partir da UAST
    fn generate_code(&self, uast: &UAST) -> Result<String, TranspileError> {
        match self.target_language.as_str() {
            "rust" => self.generate_rust(uast),
            "python" | "py" => self.generate_python(uast),
            "javascript" | "js" => self.generate_javascript(uast),
            "typescript" | "ts" => self.generate_typescript(uast),
            "c" => self.generate_c(uast),
            "cpp" | "c++" => self.generate_cpp(uast),
            "go" => self.generate_go(uast),
            "zig" => self.generate_zig(uast),
            "wasm" | "wat" => self.generate_wat(uast),
            "haskell" => self.generate_haskell(uast),
            "prolog" => self.generate_prolog(uast),
            "sql" => self.generate_sql(uast),
            _ => Err(TranspileError::UnsupportedLanguage(self.target_language.clone())),
        }
    }

    /// Otimizar UAST antes da geração
    fn optimize_uast(&mut self, uast: &UAST) -> Result<UAST, TranspileError> {
        let mut optimized = uast.clone();

        // Passo 1: Eliminar código morto
        self.dead_code_elimination(&mut optimized);

        // Passo 2: Inline de funções pequenas
        if self.config.optimization_level >= 2 {
            self.function_inlining(&mut optimized);
        }

        // Passo 3: Constant folding
        self.constant_folding(&mut optimized);

        // Passo 4: Simplificação de expressões
        if self.config.optimization_level >= 3 {
            self.expression_simplification(&mut optimized);
        }

        // Passo 5: Tail call optimization
        if self.config.optimization_level >= 2 {
            self.tail_call_optimization(&mut optimized);
        }

        Ok(optimized)
    }

    // ========================
    // OTIMIZAÇÕES
    // ========================

    fn dead_code_elimination(&mut self, uast: &mut UAST) {
        // Remover código inalcançável após return/throw
        // Remover branches que nunca são executados
        // ...
        self.optimizations_applied += 1;
    }

    fn function_inlining(&mut self, uast: &mut UAST) {
        // Substituir chamadas de funções pequenas pelo corpo
        // ...
    }

    fn constant_folding(&mut self, uast: &mut UAST) {
        // Avaliar expressões constantes em tempo de compilação
        // 2 + 3 → 5
        // true && x → x
        // ...
    }

    fn expression_simplification(&mut self, uast: &mut UAST) {
        // Simplificar expressões complexas
        // !(a == b) → a != b
        // a ? b : b → b
        // ...
    }

    fn tail_call_optimization(&mut self, uast: &mut UAST) {
        // Otimizar chamadas de cauda
        // ...
    }

    // ========================
    // GERADORES DE CÓDIGO POR LINGUAGEM
    // ========================

    fn generate_rust(&self, uast: &UAST) -> Result<String, TranspileError> {
        let mut gen = RustCodeGen::new();
        gen.generate(uast)
    }

    fn generate_python(&self, uast: &UAST) -> Result<String, TranspileError> {
        // let mut gen = PythonCodeGen::new();
        // gen.generate(uast)
        Ok(String::new())
    }

    fn generate_javascript(&self, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    fn generate_typescript(&self, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    fn generate_c(&self, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    fn generate_cpp(&self, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    fn generate_go(&self, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    fn generate_zig(&self, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    fn generate_wat(&self, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    fn generate_haskell(&self, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    fn generate_prolog(&self, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    fn generate_sql(&self, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    /// Formatar código gerado
    fn format_code(&self, code: &str) -> Result<String, TranspileError> {
        match self.target_language.as_str() {
            "rust" => self.format_with_rustfmt(code),
            "python" => self.format_with_black(code),
            "javascript" | "typescript" => self.format_with_prettier(code),
            "go" => self.format_with_gofmt(code),
            "zig" => self.format_with_zigfmt(code),
            "c" | "cpp" => self.format_with_clang_format(code),
            _ => Ok(code.to_string()),
        }
    }

    fn format_with_rustfmt(&self, code: &str) -> Result<String, TranspileError> { Ok(code.to_string()) }
    fn format_with_black(&self, code: &str) -> Result<String, TranspileError> { Ok(code.to_string()) }
    fn format_with_prettier(&self, code: &str) -> Result<String, TranspileError> { Ok(code.to_string()) }
    fn format_with_gofmt(&self, code: &str) -> Result<String, TranspileError> { Ok(code.to_string()) }
    fn format_with_zigfmt(&self, code: &str) -> Result<String, TranspileError> { Ok(code.to_string()) }
    fn format_with_clang_format(&self, code: &str) -> Result<String, TranspileError> { Ok(code.to_string()) }

    /// Verificar se linguagem é suportada
    fn is_language_supported(&self, lang: &str) -> bool {
        matches!(lang,
            "rust" | "python" | "py" | "javascript" | "js" |
            "typescript" | "ts" | "c" | "cpp" | "c++" |
            "go" | "zig" | "wasm" | "wat" | "haskell" |
            "prolog" | "sql" | "cypher" | "sparql"
        )
    }

    /// Gerar source map
    fn generate_source_map(
        &self,
        original: &UAST,
        optimized: &UAST,
    ) -> Result<String, TranspileError> {
        // Gerar mapping entre posições no código original e transpilado
        let mut map: Vec<String> = Vec::new();

        for (orig_id, orig_node) in &original.nodes {
            if let Some(opt_node) = original.nodes.get(orig_id) {
                // Mapear ranges
                // ...
            }
        }

        Ok(serde_json::to_string(&map).unwrap_or_default())
    }
}

// ============================================================================
// TRAIT CODEGENERATOR
// ============================================================================

/// Trait para geradores de código por linguagem
pub trait CodeGenerator {
    /// Gerar código a partir da UAST
    fn generate(&mut self, uast: &UAST) -> Result<String, TranspileError>;

    /// Gerar expressão
    fn gen_expr(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError>;

    /// Gerar statement
    fn gen_stmt(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError>;

    /// Gerar tipo
    fn gen_type(&mut self, type_ref: &TypeRef) -> String;

    /// Gerar padrão
    fn gen_pattern(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError>;

    /// Escrever declaração de função
    fn gen_function_decl(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError>;

    /// Escrever declaração de classe
    fn gen_class_decl(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError>;
}

// ============================================================================
// GERADORES ESPECÍFICOS (implementações parciais para demonstração)
// ============================================================================

/// Gerador Rust
pub struct RustCodeGen {
    output: String,
    indent: usize,
}

impl RustCodeGen {
    pub fn new() -> Self {
        Self {
            output: String::new(),
            indent: 0,
        }
    }

    fn emit(&mut self, code: &str) {
        self.output.push_str(&"    ".repeat(self.indent));
        self.output.push_str(code);
        self.output.push('\n');
    }

    fn emit_inline(&mut self, code: &str) {
        self.output.push_str(code);
    }
}

impl CodeGenerator for RustCodeGen {
    fn generate(&mut self, uast: &UAST) -> Result<String, TranspileError> {
        if let Some(root) = uast.nodes.get(&uast.root) {
            self.gen_program(root, uast)?;
        }
        Ok(std::mem::take(&mut self.output))
    }

    fn gen_expr(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError> {
        match &node.kind {
            NodeKind::ExprLiteral => {
                Ok(node.attributes.get("value")
                    .and_then(|v| match v {
                        AV::String(s) => Some(format!("\"{}\"", s)),
                        AV::Integer(i) => Some(i.to_string()),
                        AV::Float(f) => Some(format!("{}f64", f)),
                        AV::Boolean(b) => Some(b.to_string()),
                        _ => None,
                    })
                    .unwrap_or_default())
            }
            NodeKind::ExprIdentifier => {
                Ok(node.attributes.get("name")
                    .and_then(|v| match v { AV::String(s) => Some(s.clone()), _ => None })
                    .unwrap_or_default())
            }
            NodeKind::ExprBinary => {
                let left = node.children.get(0).and_then(|c| uast.nodes.get(c));
                let right = node.children.get(1).and_then(|c| uast.nodes.get(c));
                let op = node.attributes.get("operator")
                    .and_then(|v| match v { AV::String(s) => Some(s.as_str()), _ => None })
                    .unwrap_or("+");

                if let (Some(l), Some(r)) = (left, right) {
                    let l = self.gen_expr(l, uast)?;
                    let r = self.gen_expr(r, uast)?;
                    Ok(format!("({} {} {})", l, op, r))
                } else {
                    Ok(String::new())
                }
            }
            NodeKind::ExprCall => {
                let func_node = node.children.first()
                    .and_then(|c| uast.nodes.get(c));
                let args_nodes: Vec<&UASTNode> = node.children.iter()
                    .skip(1)
                    .filter_map(|c| uast.nodes.get(c))
                    .collect();

                if let Some(func) = func_node {
                    let func_name = self.gen_expr(func, uast)?;
                    let args: Result<Vec<_>, _> = args_nodes.iter()
                        .map(|a| self.gen_expr(a, uast))
                        .collect();

                    Ok(format!("{}({})", func_name, args?.join(", ")))
                } else {
                    Ok(String::new())
                }
            }
            NodeKind::ExprReturn => {
                let expr = node.children.first()
                    .and_then(|c| uast.nodes.get(c));
                if let Some(e) = expr {
                    Ok(format!("return {}", self.gen_expr(e, uast)?))
                } else {
                    Ok("return".to_string())
                }
            }
            NodeKind::StmtIf => {
                let cond = node.children.get(0).and_then(|c| uast.nodes.get(c));
                let then_branch = node.children.get(1).and_then(|c| uast.nodes.get(c));
                let else_branch = node.children.get(2).and_then(|c| uast.nodes.get(c));

                if let Some(c) = cond {
                    let cond_str = self.gen_expr(c, uast)?;
                    let then_str = then_branch
                        .map(|b| self.gen_expr(b, uast))
                        .transpose()?
                        .unwrap_or_default();
                    let else_str = else_branch
                        .map(|b| self.gen_expr(b, uast))
                        .transpose()?
                        .unwrap_or_default();

                    let result = if else_str.is_empty() {
                        format!("if {} {{ {} }}", cond_str, then_str)
                    } else {
                        format!("if {} {{ {} }} else {{ {} }}", cond_str, then_str, else_str)
                    };
                    Ok(result)
                } else {
                    Ok(String::new())
                }
            }
            NodeKind::StmtFor => {
                let init = node.children.get(0).and_then(|c| uast.nodes.get(c));
                let cond = node.children.get(1).and_then(|c| uast.nodes.get(c));
                let update = node.children.get(2).and_then(|c| uast.nodes.get(c));
                let body = node.children.get(3).and_then(|c| uast.nodes.get(c));

                let init_str = init.map(|i| self.gen_stmt(i, uast).unwrap_or_default())
                    .unwrap_or_default();
                let cond_str = cond.map(|c| self.gen_expr(c, uast).unwrap_or_default())
                    .unwrap_or_default();
                let update_str = update.map(|u| self.gen_stmt(u, uast).unwrap_or_default())
                    .unwrap_or_default();
                let body_str = body.map(|b| self.gen_stmt(b, uast).unwrap_or_default())
                    .unwrap_or_default();

                Ok(format!("{{ {} while({}) {{ {} {} }} }}", init_str, cond_str, body_str, update_str))
            }
            NodeKind::DeclFunction => {
                self.gen_function_decl(node, uast)
            }
            NodeKind::DeclVariable => {
                let name = node.attributes.get("name")
                    .and_then(|v| match v { AV::String(s) => Some(s), _ => None })
                    .unwrap_or(&"x");
                let is_mut = node.attributes.get("mutable")
                    .and_then(|v| match v { AV::Boolean(b) => Some(*b), _ => None })
                    .unwrap_or(false);

                let keyword = if is_mut { "let mut" } else { "let" };

                let init = node.children.first()
                    .and_then(|c| uast.nodes.get(c));

                if let Some(init_expr) = init {
                    let init_str = self.gen_expr(init_expr, uast)?;

                    if let Some(type_info) = &node.semantic_info {
                        if let Some(ref type_ref) = type_info.type_info {
                            let type_str = self.gen_type(type_ref);
                            return Ok(format!("{} {} : {} = {}", keyword, name, type_str, init_str));
                        }
                    }

                    Ok(format!("{} {} = {}", keyword, name, init_str))
                } else {
                    Ok(format!("{} {}", keyword, name))
                }
            }
            _ => {
                // Fallback: gerar como bloco genérico
                let mut result = String::new();
                for child_id in &node.children {
                    if let Some(child) = uast.nodes.get(child_id) {
                        result.push_str(&self.gen_expr(child, uast)?);
                        result.push('\n');
                    }
                }
                Ok(result)
            }
        }
    }

    fn gen_stmt(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError> {
        self.gen_expr(node, uast)
    }

    fn gen_type(&mut self, type_ref: &TypeRef) -> String {
        match &type_ref.name[..] {
            "i32" => "i32".to_string(),
            "f64" => "f64".to_string(),
            "bool" => "bool".to_string(),
            "string" => "String".to_string(),
            "()" => "()".to_string(),
            name => name.to_string(),
        }
    }

    fn gen_pattern(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError> {
        self.gen_expr(node, uast)
    }

    fn gen_function_decl(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError> {
        let name = node.attributes.get("name")
            .and_then(|v| match v { AV::String(s) => Some(s), _ => None })
            .unwrap_or(&"fn");

        let params: Vec<String> = node.children.iter()
            .filter_map(|c| uast.nodes.get(c))
            .filter(|c| matches!(c.kind, NodeKind::DeclVariable))
            .map(|c| self.gen_expr(c, uast))
            .collect::<Result<_, _>>()?;

        let return_type = if let Some(ref si) = node.semantic_info {
            if let Some(ref tr) = si.type_info {
                format!(" -> {}", self.gen_type(tr))
            } else {
                String::new()
            }
        } else {
            String::new()
        };

        let body = node.children.iter()
            .find(|c| uast.nodes.get(*c).map(|n| !matches!(n.kind, NodeKind::DeclVariable)).unwrap_or(false))
            .and_then(|c| uast.nodes.get(c))
            .map(|b| self.gen_expr(b, uast))
            .transpose()?
            .unwrap_or_else(|| "()".to_string());

        Ok(format!(
            "fn {}({}){} {{\n    {}\n}}",
            name,
            params.join(", "),
            return_type,
            body
        ))
    }

    fn gen_class_decl(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError> {
        Ok(String::new())
    }

    fn gen_program(&mut self, node: &UASTNode, uast: &UAST) -> Result<String, TranspileError> {
        self.emit("// Transpilado pelo ARKHE Polymath-Polyglot Parser");
        self.emit("#![allow(unused)]");
        self.emit("");

        for child_id in &node.children {
            if let Some(child) = uast.nodes.get(child_id) {
                match &child.kind {
                    NodeKind::DeclFunction => {
                        self.emit(&self.gen_function_decl(child, uast)?);
                    }
                    NodeKind::DeclVariable => {
                        self.emit(&self.gen_expr(child, uast)?);
                    }
                    _ => {}
                }
            }
        }

        Ok(std::mem::take(&mut self.output))
    }
}

impl Default for RustCodeGen {
    fn default() -> Self { Self::new() }
}


#[derive(Debug, thiserror::Error)]
pub enum TranspileError {
    #[error("Linguagem não suportada: {0}")]
    UnsupportedLanguage(String),

    #[error("Erro de parsing: {0}")]
    ParseError(String),

    #[error("Erro de geração: {0}")]
    GenerationError(String),

    #[error("Erro de formatação: {0}")]
    FormatError(String),

    #[error("UAST inválido: {0}")]
    InvalidUAST(String),
}
