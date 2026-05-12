// ============================================================================
// ARKHE P³ v3 — Lark-to-Rust Grammar Compiler
// ============================================================================
// Compila gramáticas PEG do formato Lark (.lark) diretamente para
// código Rust otimizado, eliminando dependências de runtime de parsing.
//
// Pipeline:
//   .lark → Lark AST → LarkToRust IR → Rust AST → Tokenize + Parse
//
// Vantagens sobre interpretação:
//   - Zero overhead de interpretação em runtime
//   - Compilação AOT (Ahead-Of-Time) para máxima performance
//   - Type-checking da gramática em tempo de compilação
//   - Sem dependências externas em produção
// ============================================================================

use std::collections::BTreeMap;
use std::fmt::Write as FmtWrite;
use std::fs;
use std::path::Path;

// ============================================================================
// ESTRUTURAS INTERMEDIÁRIAS (IR)
// ============================================================================

/// Representação intermediária de uma gramática Lark
#[derive(Debug, Clone)]
pub struct LarkGrammar {
    pub name: String,
    pub start_rules: Vec<String>,
    pub rules: BTreeMap<String, Rule>,
    pub terminals: BTreeMap<String, TerminalDef>,
    pub options: GrammarOptions,
    pub imports: Vec<String>,
    pub ignore: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct Rule {
    pub name: String,
    pub expressions: Vec<Expression>,
    pub is_inline: bool,
    pub is_fragment: bool,
    pub visibility: Visibility,
    pub origin: Option<String>, // Para regras parametrizadas
    pub keep_tree_node: bool,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Expression {
    pub kind: ExprKind,
    pub quantifier: Quantifier,
    pub label: Option<String>,
    pub filter: Option<String>, // Para predicados semânticos
}

#[derive(Debug, Clone, PartialEq)]
pub enum ExprKind {
    Terminal(String),
    NonTerminal(String),
    Sequence(Vec<Expression>),
    Alternative(Vec<Expression>),
    Optional(Box<Expression>),
    Repeat(Box<Expression>),     // *
    RepeatOnce(Box<Expression>), // +
    Maybe(Box<Expression>),      // ?
    Group(Box<Expression>),
    Lookahead(Box<Expression>, bool), // positive/negative
    Regex(String),
    Template(String, Vec<String>), // Template usage com args
    Epsilon,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Quantifier {
    Once,       // exatamente uma vez (padrão)
    Optional,   // ?
    ZeroOrMore, // *
    OneOrMore,  // +
}

#[derive(Debug, Clone, PartialEq)]
pub enum Visibility {
    Public,
    Private,
    Hidden(String), // hidden por inline
}

#[derive(Debug, Clone)]
pub struct TerminalDef {
    pub name: String,
    pub pattern: RegexPattern,
    pub flags: TerminalFlags,
}

#[derive(Debug, Clone, PartialEq)]
pub enum RegexPattern {
    Raw(String),              // Padrão regex literal
    Flags(Vec<FlaggedRegex>), // Multiplos padrões com flags
}

#[derive(Debug, Clone, PartialEq)]
pub struct FlaggedRegex {
    pub pattern: String,
    pub flags: TerminalFlags,
}

#[derive(Debug, Clone, Default, PartialEq)]
pub struct TerminalFlags {
    pub case_insensitive: bool,
    pub unicode: bool,
    pub dot_all: bool,
    pub verbose: bool,
}

#[derive(Debug, Clone)]
pub struct GrammarOptions {
    pub case_insensitive: bool,
    pub always_keep_all_tokens: bool,
    pub ambiguity: AmbiguityMode,
    pub regex: bool,
    pub keep_all_tokens: bool,
    pub maybe_placeholders: bool,
    pub g_regex_flags: Vec<String>,
    pub no_parse_ambiguity: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AmbiguityMode {
    Earley, // Padrão
    LALR,   // LALR(1)
    Auto,   // Escolha automática
}

// ============================================================================
// PARSER DA GRAMÁTICA LARK
// ============================================================================

/// Parser da sintaxe .lark — converte texto Lark em LarkGrammar IR
pub struct LarkParser {
    grammar: LarkGrammar,
    errors: Vec<LarkParseError>,
}

#[derive(Debug, Clone)]
pub struct LarkParseError {
    pub line: usize,
    pub column: usize,
    pub message: String,
    pub context: Option<String>,
}

impl LarkParser {
    /// Parse de um arquivo .lark
    pub fn parse_file(path: &Path) -> Result<LarkGrammar, Vec<LarkParseError>> {
        let content = fs::read_to_string(path).map_err(|e| {
            vec![LarkParseError {
                line: 0,
                column: 0,
                message: format!("Failed to read file: {}", e),
                context: None,
            }]
        })?;

        Self::parse_str(
            &content,
            path.file_stem()
                .and_then(|n| n.to_str())
                .unwrap_or("grammar"),
        )
    }

    /// Parse de string Lark
    pub fn parse_str(content: &str, name: &str) -> Result<LarkGrammar, Vec<LarkParseError>> {
        let mut parser = Self {
            grammar: LarkGrammar {
                name: name.to_string(),
                start_rules: Vec::new(),
                rules: BTreeMap::new(),
                terminals: BTreeMap::new(),
                options: GrammarOptions {
                    case_insensitive: false,
                    always_keep_all_tokens: false,
                    ambiguity: AmbiguityMode::Earley,
                    regex: false,
                    keep_all_tokens: false,
                    maybe_placeholders: false,
                    g_regex_flags: Vec::new(),
                    no_parse_ambiguity: false,
                },
                imports: Vec::new(),
                ignore: Vec::new(),
            },
            errors: Vec::new(),
        };

        parser.parse_content(content);

        if parser.errors.is_empty() {
            Ok(parser.grammar)
        } else {
            Err(parser.errors)
        }
    }

    fn parse_content(&mut self, content: &str) {
        let mut lines = content.lines().peekable();

        while let Some(line) = lines.next() {
            let trimmed = line.trim();

            // Ignorar linhas vazias e comentários
            if trimmed.is_empty() || trimmed.starts_with("//") || trimmed.starts_with("#|") {
                continue;
            }

            // Multiline comment
            if trimmed.starts_with("/|") {
                while let Some(l) = lines.next() {
                    if l.trim().ends_with("|/") {
                        break;
                    }
                }
                continue;
            }

            // Directives
            if trimmed.starts_with('%') {
                self.parse_directive(trimmed);
                continue;
            }

            // Ignore directive inline
            if trimmed.starts_with("|") {
                // Continuation of previous rule
                continue;
            }

            // Regra ou terminal
            if let Some(colon_pos) = trimmed.find(':') {
                let name_part = &trimmed[..colon_pos].trim();
                let body = &trimmed[colon_pos + 1..].trim();

                if name_part
                    .chars()
                    .all(|c| c.is_uppercase() || c.is_ascii_digit() || c == '_' || c == '!')
                {
                    // Terminal (UPPER_CASE)
                    self.parse_terminal(name_part, body);
                } else {
                    // Regra (camelCase ou snake_case)
                    self.parse_rule(name_part, body);
                }
            }
        }
    }

    fn parse_directive(&mut self, line: &str) {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.is_empty() {
            return;
        }

        match parts[0] {
            "%start" => {
                if parts.len() > 1 {
                    self.grammar.start_rules = parts[1..].iter().map(|s| s.to_string()).collect();
                }
            }
            "%import" => {
                let import = parts[1..].join(" ");
                self.grammar.imports.push(import);
            }
            "%ignore" => {
                self.grammar.ignore.push(parts[1..].join(" "));
            }
            "%common" => {
                // Regras comuns (visíveis apenas internamente)
            }
            "%inline" => {
                // Marca próxima regra como inline
            }
            "%left" | "%right" | "%nonassoc" => {
                // Precedência de operadores (para variantes LALR)
            }
            _ => {}
        }
    }

    fn parse_terminal(&mut self, name: &str, body: &str) {
        // Processar corpo do terminal (regex)
        let pattern = self.extract_regex(body);

        self.grammar.terminals.insert(
            name.to_string(),
            TerminalDef {
                name: name.to_string(),
                pattern: RegexPattern::Raw(pattern),
                flags: TerminalFlags::default(),
            },
        );
    }

    fn parse_rule(&mut self, name: &str, body: &str) {
        let expressions = self.parse_expressions(body);

        // Detecção de inline
        let is_inline = name.starts_with('_') || body.contains("->");

        self.grammar.rules.insert(
            name.to_string(),
            Rule {
                name: name.to_string(),
                expressions,
                is_inline,
                is_fragment: name.starts_with('_'),
                visibility: if is_inline {
                    Visibility::Hidden("inline".into())
                } else {
                    Visibility::Public
                },
                origin: None,
                keep_tree_node: true,
            },
        );
    }

    fn parse_expressions(&self, body: &str) -> Vec<Expression> {
        // Parser simplificado de expressões Lark
        // Suporta: alternatives, sequences, quantifiers, groups, lookahead

        let mut expressions = Vec::new();

        // Split por '|' para alternatives
        let alternatives: Vec<&str> = body.split('|').map(str::trim).collect();

        if alternatives.len() == 1 {
            // Única expressão (pode ser sequência)
            let expr = self.parse_single_expr(alternatives[0]);
            expressions.push(expr);
        } else {
            // Alternative
            let mut alt_exprs = Vec::new();
            for alt in alternatives {
                alt_exprs.push(self.parse_single_expr(alt));
            }
            expressions.push(Expression {
                kind: ExprKind::Alternative(alt_exprs),
                quantifier: Quantifier::Once,
                label: None,
                filter: None,
            });
        }

        expressions
    }

    fn parse_single_expr(&self, text: &str) -> Expression {
        let text = text.trim();

        if text.is_empty() {
            return Expression {
                kind: ExprKind::Epsilon,
                quantifier: Quantifier::Once,
                label: None,
                filter: None,
            };
        }

        // Detectar quantificador no final
        let (body, quantifier) = self.extract_quantifier(text);

        // Parse do body
        let kind = if body.starts_with('(') && body.ends_with(')') {
            // Grupo
            let inner = &body[1..body.len() - 1];
            let inner_exprs = self.parse_expressions(inner);

            if inner_exprs.len() == 1 {
                match inner_exprs.into_iter().next().unwrap().kind {
                    ExprKind::Sequence(items) => ExprKind::Group(Box::new(Expression {
                        kind: ExprKind::Sequence(items),
                        quantifier: Quantifier::Once,
                        label: None,
                        filter: None,
                    })),
                    other => ExprKind::Group(Box::new(Expression {
                        kind: other,
                        quantifier: Quantifier::Once,
                        label: None,
                        filter: None,
                    })),
                }
            } else {
                ExprKind::Group(Box::new(Expression {
                    kind: ExprKind::Alternative(inner_exprs),
                    quantifier: Quantifier::Once,
                    label: None,
                    filter: None,
                }))
            }
        } else if body.starts_with('{') && body.ends_with('}') {
            // Regra especial ou código inline — tratar como epsi para simplificar
            // Em produção: integrar com semantic actions
            ExprKind::Epsilon
        } else if body.starts_with('!') {
            // Negative lookahead
            let inner = &body[1..];
            ExprKind::Lookahead(
                Box::new(Expression {
                    kind: ExprKind::NonTerminal(inner.trim().to_string()),
                    quantifier: Quantifier::Once,
                    label: None,
                    filter: None,
                }),
                false,
            )
        } else if body.starts_with('~') {
            // Positive lookahead
            let inner = &body[1..];
            ExprKind::Lookahead(
                Box::new(Expression {
                    kind: ExprKind::NonTerminal(inner.trim().to_string()),
                    quantifier: Quantifier::Once,
                    label: None,
                    filter: None,
                }),
                true,
            )
        } else if body.contains(' ') {
            // Sequence — tokens separados por espaço
            let tokens: Vec<&str> = body.split_whitespace().collect();
            let items: Vec<Expression> = tokens
                .iter()
                .map(|t| Expression {
                    kind: ExprKind::NonTerminal(t.to_string()),
                    quantifier: Quantifier::Once,
                    label: None,
                    filter: None,
                })
                .collect();

            if items.len() == 1 {
                items.into_iter().next().unwrap().kind
            } else {
                ExprKind::Sequence(items)
            }
        } else {
            // Terminal ou Non-Terminal simples
            if body.starts_with('"') || body.starts_with('\'') {
                // Terminal literal
                let literal = body.trim_matches(|c| c == '"' || c == '\'');
                ExprKind::Terminal(format!(
                    "LIT_{}",
                    literal.replace(|c: char| !c.is_alphanumeric(), "_")
                ))
            } else if body
                .chars()
                .all(|c| c.is_uppercase() || c.is_ascii_digit() || c == '_' || c == '!')
            {
                // Terminal (referencia)
                ExprKind::Terminal(body.to_string())
            } else {
                // Non-terminal
                ExprKind::NonTerminal(body.to_string())
            }
        };

        // Verificar label (como "rule"? ou "rule=value")
        let label = if let Some(pos) = text.find("?:") {
            Some(text[..pos].trim().to_string())
        } else if let Some(pos) = text.find('?') {
            if pos + 1 < text.len()
                && &text[pos + 1..pos + 2] != "?"
                && &text[pos + 1..pos + 2] != "*"
                && &text[pos + 1..pos + 2] != "+"
            {
                Some(text[..pos].trim().to_string())
            } else {
                None
            }
        } else {
            None
        };

        // Verificar filter (como "rule{condition}")
        let filter = if text.contains('{') && text.contains('}') {
            let start = text.find('{').unwrap();
            let end = text.rfind('}').unwrap();
            if start < end {
                Some(text[start + 1..end].to_string())
            } else {
                None
            }
        } else {
            None
        };

        Expression {
            kind,
            quantifier,
            label,
            filter,
        }
    }

    fn extract_quantifier<'a>(&self, text: &'a str) -> (&'a str, Quantifier) {
        let last_char = text.chars().last();
        match last_char {
            Some('?') => (&text[..text.len() - 1], Quantifier::Optional),
            Some('*') => (&text[..text.len() - 1], Quantifier::ZeroOrMore),
            Some('+') => (&text[..text.len() - 1], Quantifier::OneOrMore),
            _ => (text, Quantifier::Once),
        }
    }

    fn extract_regex(&self, body: &str) -> String {
        // Extrair padrão regex do corpo do terminal
        // Suporta: /regex/, "", e regex inline
        let trimmed = body.trim();

        if trimmed.starts_with('/') {
            // Padrão: /regex/
            if let Some(end) = trimmed[1..].find('/') {
                trimmed[1..1 + end].to_string()
            } else {
                trimmed[1..].to_string()
            }
        } else if trimmed.starts_with('"') || trimmed.starts_with('\'') {
            // String literal — converter para regex literal
            let lit = trimmed.trim_matches(|c| c == '"' || c == '\'');
            regex::escape(lit)
        } else {
            // Regex inline ou referência a outro terminal
            trimmed.to_string()
        }
    }
}

// ============================================================================
// GERADOR DE CÓDIGO RUST A PARTIR DE GRAMÁTICA LARK
// ============================================================================

#[derive(Debug, thiserror::Error)]
pub enum CompilerError {
    #[error("Parse error: {0}")]
    ParseError(String),

    #[error("Generation error: {0}")]
    GenerationError(String),

    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Invalid grammar: {0}")]
    InvalidGrammar(String),

    #[error("Multiple Parse Errors")]
    MultipleParseErrors(Vec<LarkParseError>),
}

impl From<Vec<LarkParseError>> for CompilerError {
    fn from(errs: Vec<LarkParseError>) -> Self {
        CompilerError::MultipleParseErrors(errs)
    }
}

/// Compila gramática Lark para código Rust otimizado
pub struct LarkToRustCompiler {
    grammar: LarkGrammar,
    config: CompilerConfig,
}

#[derive(Clone, Debug)]
pub struct CompilerConfig {
    /// Otimização: inline small rules
    pub inline_threshold: usize, // Tamanho máximo para inline

    /// Otimização: merge de alternativas com prefixo comum
    pub enable_prefix_merging: bool,

    /// Otimização: packrat parsing (memoization)
    pub enable_packrat: bool,

    /// Gerar código SIMD para matching de strings
    pub enable_simd: bool,

    /// Target: "parser" (parser completo) ou "tokenizer" (apenas tokenizer)
    pub target: CompileTarget,

    /// Output format
    pub format: OutputFormat,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CompileTarget {
    Parser,    // Parser completo + tokenizer
    Tokenizer, // Apenas tokenizer
    Both,      // Ambos em módulos separados
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum OutputFormat {
    SourceFile, // Arquivo .rs standalone
    Module,     // Module para incluir em crate existente
    WasmReady,  // Otimizado para compilação Wasm
}

impl Default for CompilerConfig {
    fn default() -> Self {
        Self {
            inline_threshold: 5,
            enable_prefix_merging: true,
            enable_packrat: true,
            enable_simd: true,
            target: CompileTarget::Parser,
            format: OutputFormat::SourceFile,
        }
    }
}

impl LarkToRustCompiler {
    /// Criar novo compilador
    pub fn new(grammar: LarkGrammar) -> Self {
        Self {
            grammar,
            config: CompilerConfig::default(),
        }
    }

    /// Compilar gramática para código Rust
    pub fn compile(&self) -> Result<String, CompilerError> {
        let mut output = String::new();

        // Gerar cabeçalho
        self.generate_header(&mut output);

        // Gerar tipos de dados
        self.generate_types(&mut output);

        // Gerar tokenizer
        if matches!(
            self.config.target,
            CompileTarget::Parser | CompileTarget::Both | CompileTarget::Tokenizer
        ) {
            self.generate_tokenizer(&mut output);
        }

        // Gerar parser
        if matches!(
            self.config.target,
            CompileTarget::Parser | CompileTarget::Both
        ) {
            self.generate_parser(&mut output)?;
        }

        // Gerar implementação AST
        self.generate_ast(&mut output);

        // Gerar utility functions
        self.generate_utilities(&mut output);

        Ok(output)
    }

    /// Compilar arquivo .lark diretamente
    pub fn compile_file(
        path: &Path,
        config: Option<CompilerConfig>,
    ) -> Result<String, CompilerError> {
        let grammar = LarkParser::parse_file(path)?;
        // Salvar IR para depuração
        // Self::save_ir(&grammar, path)?;

        let mut compiler = Self::new(grammar);
        if let Some(c) = config {
            compiler.config = c;
        }
        compiler.compile()
    }

    fn generate_header(&self, output: &mut String) {
        let name = self.grammar.name.to_uppercase();
        writeln!(
            output,
            r#"// ============================================================================
// ARKHE P³ — Lark-to-Rust Compiled Grammar: {}
// Gerado automaticamente por lark-to-rust
// NÃO EDITAR MANUALMENTE — editar o arquivo .lark original
// ============================================================================

#![allow(clippy::too_many_arguments)]
#![allow(clippy::type_complexity)]
#![allow(clippy::needless_borrow)]
#![cfg_attr(feature = "wasm", no_std)]

use core::option::Option::Some;
use core::result::Result::Ok;
"#,
            name
        )
        .unwrap();

        if self.config.enable_packrat {
            write!(
                output,
                r#"
// Packrat parsing: memoization para parsing linear
use core::cell::RefCell;
use core::collections::HashMap;
"#
            )
            .unwrap();
        }

        if self.config.enable_simd {
            write!(
                output,
                r#"
// SIMD optimizations (when available)
#[cfg(target_feature = "simd128")]
use core::arch::wasm32::*;
"#
            )
            .unwrap();
        }

        writeln!(
            output,
            r#"
// ============================================================================
// TIPOS DO PARSER
// ============================================================================

/// Resultado do parsing
pub type ParseResult<T> = Result<T, ParseError>;

/// Erro de parsing com localização
#[derive(Clone, Debug, PartialEq)]
pub struct ParseError {{
    pub line: u32,
    pub column: u32,
    pub message: &'static str,
    pub expected: Vec<&'static str>,
}}

/// Localização no texto fonte
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Location {{
    pub line: u32,
    pub column: u32,
    pub offset: usize,
}}

/// Token reconhecido pelo lexer
#[derive(Clone, Debug, PartialEq)]
pub enum Token {{
"#
        )
        .unwrap();

        // Gerar variantes de Token para cada terminal
        for (name, _) in &self.grammar.terminals {
            writeln!(output, "    /// Terminal: {}\n    {}(String),", name, name).unwrap();
        }
        writeln!(
            output,
            r#"
    /// Identificador não reconhecido
    Unknown(String),

    /// Fim do input
    Eof,
}}

/// Representação do token com localização
#[derive(Clone, Debug)]
pub struct TokenSpan {{
    pub token: Token,
    pub location: Location,
    pub text: String,
}}
"#
        )
        .unwrap();
    }

    fn generate_types(&self, output: &mut String) {
        writeln!(
            output,
            r#"
// ============================================================================
// ESTRUTURAS DE PARSER
// ============================================================================

/// Parser principal para a gramática {}
pub struct {}Parser {{
    input: Vec<u16>,          // Input caractere por caractere
    position: usize,
    line: u32,
    column: u32,
"#,
            self.grammar.name.to_uppercase(),
            self.grammar.name.to_uppercase()
        )
        .unwrap();

        if self.config.enable_packrat {
            write!(
                output,
                r#"    memo: RefCell<HashMap<(usize, u32), Option<usize>>>,
    expected: RefCell<Vec<&'static str>>,
"#
            )
            .unwrap();
        }

        write!(
            output,
            r#"}}

impl {}Parser {{
    pub fn new(input: &[u8]) -> Self {{
        Self {{
            input: input.iter().map(|&b| b as u16).collect(),
            position: 0,
            line: 1,
            column: 1,
"#,
            self.grammar.name.to_uppercase()
        )
        .unwrap();

        if self.config.enable_packrat {
            write!(
                output,
                r#"            memo: RefCell::new(HashMap::new()),
            expected: RefCell::new(Vec::new()),
"#
            )
            .unwrap();
        }

        write!(
            output,
            r#"        }}
    }}

"#
        )
        .unwrap();
    }

    fn generate_tokenizer(&self, output: &mut String) {
        writeln!(
            output,
            r#"
// ============================================================================
// LEXER / TOKENIZER
// ============================================================================

impl {}Parser {{
    /// Tokenize o input inteiro
    pub fn tokenize(&mut self) -> ParseResult<Vec<TokenSpan>> {{
        let mut tokens = Vec::new();

        while !self.is_eof() {{
            self.skip_whitespace();
            self.skip_comments();

            if self.is_eof() {{
                break;
            }}

            let start_loc = self.current_location();
            let token = self.scan_token()?;

            tokens.push(TokenSpan {{
                token,
                location: start_loc,
                text: self.text_from(start_loc.offset),
            }});
        }}

        tokens.push(TokenSpan {{
            token: Token::Eof,
            location: self.current_location(),
            text: String::new(),
        }});

        Ok(tokens)
    }}

    /// Scan de um único token (sem estado)
    fn scan_token(&mut self) -> ParseResult<Token> {{
"#,
            self.grammar.name.to_uppercase()
        )
        .unwrap();

        // Gerar matching de terminais
        for (name, terminal) in &self.grammar.terminals {
            if let RegexPattern::Raw(pattern) = &terminal.pattern {
                writeln!(
                    output,
                    r#"
        // {}: {}
        if self.starts_with_pattern("{}", {}) {{
            let text = self.consume_match("{}");
            return Ok(Token::{}(text));
        }}
"#,
                    name,
                    pattern,
                    pattern.replace("\\", "\\\\").replace("\"", "\\\""),
                    terminal.flags.case_insensitive,
                    pattern.replace("\\", "\\\\").replace("\"", "\\\""),
                    name
                )
                .unwrap();
            }
        }

        writeln!(
            output,
            r#"
        // Fallback: caractere desconhecido
        let _ch = self.peek_char();
        let pos = self.current_location();
        self.advance(1);
        Err(ParseError {{
            line: pos.line,
            column: pos.column,
            message: "Caractere inesperado",
            expected: vec![],
        }})
    }}

    /// Pular whitespace
    fn skip_whitespace(&mut self) {{
        while !self.is_eof() {{
            match self.peek_char() {{
                ' ' | '\t' | '\r' => {{ self.advance(1); self.column += 1; }},
                '\n' => {{ self.advance(1); self.line += 1; self.column = 1; }},
                _ => break,
            }}
        }}
    }}

    /// Pular comentários
    fn skip_comments(&mut self) {{
        if self.peek_str("//") {{
            while !self.is_eof() && self.peek_char() != '\n' {{
                self.advance(1);
            }}
        }}
    }}

    /// Verificar se input começa com determinado padrão
    fn starts_with_pattern(&self, pattern: &str, case_insensitive: bool) -> bool {{
        if case_insensitive {{
            self.input[self.position..]
                .iter()
                .take(pattern.len())
                .map(|&c| c as u8 as char)
                .collect::<String>()
                .to_lowercase()
                == pattern.to_lowercase()
        }} else {{
            self.starts_with(pattern)
        }}
    }}

    /// Consumir match e avançar posição
    fn consume_match(&mut self, pattern: &str) -> String {{
        let text: String = self.input[self.position..self.position + pattern.len()]
            .iter()
            .map(|&c| c as u8 as char)
            .collect();

        // Verificar que o match não continua (word boundary)
        if self.position + pattern.len() < self.input.len() {{
            let next = self.input[self.position + pattern.len()] as u8 as char;
            if next.is_alphanumeric() || next == '_' {{
                // Não é um match válido (partial identifier)
                self.advance(1);
                return String::new(); // Trigger retry
            }}
        }}

        let result = text.clone();
        for _ in 0..pattern.len() {{
            let ch = self.input[self.position] as u8 as char;
            self.advance(1);
            if ch == '\n' {{
                self.line += 1;
                self.column = 1;
            }} else {{
                self.column += 1;
            }}
        }}
        result
    }}
"#
        )
        .unwrap();
    }

    fn generate_parser(&self, output: &mut String) -> Result<(), CompilerError> {
        writeln!(
            output,
            r#"
// ============================================================================
// PARSER RECURSIVE DESCENT (Gerado do Lark)
// ============================================================================
"#
        )
        .unwrap();

        // Métodos auxiliares
        writeln!(
            output,
            r#"
impl {}Parser {{
    // Helpers básicos
    fn is_eof(&self) -> bool {{
        self.position >= self.input.len()
    }}

    fn peek_char(&self) -> char {{
        if self.is_eof() {{ '\0' }} else {{ self.input[self.position] as u8 as char }}
    }}

    fn peek_str(&self, s: &str) -> bool {{
        let bytes = s.as_bytes();
        self.position + bytes.len() <= self.input.len()
            && self.input[self.position..self.position + bytes.len()]
                .iter()
                .zip(bytes.iter())
                .all(|(&a, &b)| a as u8 == b)
    }}

    fn starts_with(&self, s: &str) -> bool {{
        let bytes = s.as_bytes();
        self.position + bytes.len() <= self.input.len()
            && self.input[self.position..self.position + bytes.len()]
                .iter()
                .zip(bytes.iter())
                .all(|(&a, &b)| a as u8 == b)
    }}

    fn advance(&mut self, n: usize) {{
        self.position += n;
    }}

    fn current_location(&self) -> Location {{
        Location {{
            line: self.line,
            column: self.column,
            offset: self.position,
        }}
    }}

    fn text_from(&self, offset: usize) -> String {{
        self.input[offset..self.position]
            .iter()
            .map(|&c| c as u8 as char)
            .collect()
    }}

    fn expect(&mut self, s: &str) -> ParseResult<()> {{
        if self.peek_str(s) {{
            for _ in 0..s.len() {{ self.advance(1); }}
            Ok(())
        }} else {{
            Err(ParseError {{
                line: self.line,
                column: self.column,
                message: "Token inesperado",
                expected: vec![s],
            }})
        }}
    }}
"#,
            self.grammar.name.to_uppercase()
        )
        .unwrap();

        // Packrat memoization helpers
        if self.config.enable_packrat {
            writeln!(
                output,
                r#"
    // Packrat parsing helpers
    fn memo_lookup(&self, pos: usize, rule_id: u32) -> Option<Option<usize>> {{
        let memo = self.memo.borrow();
        memo.get(&(pos, rule_id)).copied()
    }}

    fn memo_insert(&self, pos: usize, rule_id: u32, result: Option<usize>) {{
        self.memo.borrow_mut().insert((pos, rule_id), result);
    }}

    fn add_expected(&self, expected: &'static str) {{
        let mut exp = self.expected.borrow_mut();
        if !exp.contains(&expected) {{
            exp.push(expected);
        }}
    }}
"#
            )
            .unwrap();
        }

        writeln!(output, "}}").unwrap();

        // Gerar cada regra como método
        for (name, rule) in &self.grammar.rules {
            if rule.is_inline {
                continue;
            } // Skip inline rules

            self.generate_rule_method(output, name, rule)?;
        }
        Ok(())
    }

    fn generate_rule_method(
        &self,
        output: &mut String,
        name: &str,
        rule: &Rule,
    ) -> Result<(), CompilerError> {
        let rule_id = self.compute_rule_id(name);

        writeln!(
            output,
            r#"
impl {}Parser {{
// Regra: {name}
fn parse_rule_{name_snake}(&mut self) -> ParseResult<()> {{
"#,
            self.grammar.name.to_uppercase(),
            name = name,
            name_snake = name.replace("-", "_")
        )
        .unwrap();

        if self.config.enable_packrat {
            writeln!(
                output,
                r#"
    // Packrat: check memo
    let pos = self.position;
    if let Some(cached) = self.memo_lookup(pos, {rule_id}) {{
        if let Some(end_pos) = cached {{
            self.position = end_pos;
            return Ok(());
        }} else {{
            return Err(ParseError {{
                line: self.line,
                column: self.column,
                message: "Memoized failure",
                expected: vec![],
            }});
        }}
    }}
    let _before_pos = self.position;
"#
            )
            .unwrap();
        }

        // Gerar body da regra
        for expr in &rule.expressions {
            self.generate_expression(output, expr, 1)?;
        }

        if self.config.enable_packrat {
            writeln!(
                output,
                r#"
    // Packrat: save success
    self.memo_insert(pos, {rule_id}, Some(self.position));
"#
            )
            .unwrap();
        }

        writeln!(
            output,
            r#"    Ok(())
}}
}}"#
        )
        .unwrap();

        Ok(())
    }

    fn generate_expression(
        &self,
        output: &mut String,
        expr: &Expression,
        indent: usize,
    ) -> Result<(), CompilerError> {
        let pad = "    ".repeat(indent);

        match &expr.kind {
            ExprKind::Sequence(items) => {
                // Sequência: gerar cada item em ordem
                for item in items {
                    self.generate_expression(output, item, indent)?;
                }
            }

            ExprKind::Alternative(items) => {
                // Alternativa: gerar if/else chain
                for (i, item) in items.iter().enumerate() {
                    if i == 0 {
                        writeln!(output, "{}// Alternative branch {}", pad, i).unwrap();
                        writeln!(output, "{}let mut _success = false;", pad).unwrap();
                        writeln!(output, "{}if !_success {{", pad).unwrap();
                    } else {
                        writeln!(output, "{}if !_success {{", pad).unwrap();
                    }
                    self.generate_expression(output, item, indent + 1)?;
                    writeln!(output, "{}    _success = true;", pad).unwrap();
                    if i < items.len() - 1 {
                        writeln!(output, "{}}}", pad).unwrap();
                    }
                }
                writeln!(output, "{}}}", pad).unwrap();
            }

            ExprKind::Terminal(name) => {
                writeln!(
                    output,
                    r#"{}// Terminal: {}
{}self.expect("{}")?;"#,
                    pad, name, pad, name
                )
                .unwrap();
            }

            ExprKind::NonTerminal(name) => {
                // Verificar se é regra inline (substituir) ou chamada normal
                if let Some(target_rule) = self.grammar.rules.get(name) {
                    if target_rule.is_inline {
                        // Inline: substituir body
                        for inline_expr in &target_rule.expressions {
                            self.generate_expression(output, inline_expr, indent)?;
                        }
                    } else {
                        writeln!(
                            output,
                            r#"{}self.parse_rule_{}()?;"#,
                            pad,
                            name.replace("-", "_")
                        )
                        .unwrap();
                    }
                } else {
                    writeln!(
                        output,
                        r#"{}// Non-terminal: {} (forward reference)
{}self.parse_rule_{}()?;"#,
                        pad,
                        name,
                        pad,
                        name.replace("-", "_")
                    )
                    .unwrap();
                }
            }

            ExprKind::Optional(inner) => {
                writeln!(output, "{}// Optional", pad).unwrap();
                writeln!(output, "{}{{", pad).unwrap();
                writeln!(output, "{}    let saved_pos = self.position;", pad).unwrap();
                writeln!(output, "{}    if self.parse_optional(|| {{", pad).unwrap();
                self.generate_expression(output, inner, indent + 2)?;
                writeln!(output, "{}        Ok(())", pad).unwrap();
                writeln!(output, "{}    }}).is_err() {{", pad).unwrap();
                writeln!(output, "{}        self.position = saved_pos;", pad).unwrap();
                writeln!(output, "{}    }}", pad).unwrap();
                writeln!(output, "{}}}", pad).unwrap();
            }

            ExprKind::Repeat(inner) | ExprKind::RepeatOnce(inner) | ExprKind::Maybe(inner) => {
                let is_repeat = matches!(expr.kind, ExprKind::Repeat(_));
                let loop_start = if is_repeat { "loop" } else { "loop" };
                let name = match &inner.kind {
                    ExprKind::Terminal(n) => n.clone(),
                    ExprKind::NonTerminal(n) => n.clone(),
                    _ => "item".to_string(),
                };
                writeln!(
                    output,
                    "{}// Repeat ({})",
                    pad,
                    if is_repeat {
                        "zero or more"
                    } else {
                        "one or more"
                    }
                )
                .unwrap();
                writeln!(output, "{}let mut count_{} = 0usize;", pad, name).unwrap();
                writeln!(output, "{}{} {{", pad, loop_start).unwrap();
                writeln!(output, "{}    let saved_pos = self.position;", pad).unwrap();
                writeln!(output, "{}    match self.parse_optional(|| {{", pad).unwrap();

                self.generate_expression(output, inner, indent + 2)?;

                writeln!(output, "{}        Ok(())", pad).unwrap();
                writeln!(output, "{}    }}) {{", pad).unwrap();
                writeln!(output, "{}        Ok(()) => count_{} += 1,", pad, name).unwrap();
                writeln!(output, "{}        Err(_) => {{", pad).unwrap();
                writeln!(output, "{}            self.position = saved_pos;", pad).unwrap();
                writeln!(output, "{}            break;", pad).unwrap();
                writeln!(output, "{}        }}", pad).unwrap();
                writeln!(output, "{}    }}", pad).unwrap();
                writeln!(output, "{}}}", pad).unwrap();
                if !matches!(expr.kind, ExprKind::Repeat(_))
                    && !matches!(expr.kind, ExprKind::Maybe(_))
                {
                    writeln!(output, "{}if count_{} == 0 {{", pad, name).unwrap();
                    writeln!(output, "{}    return Err(ParseError {{", pad).unwrap();
                    writeln!(output, "{}        line: self.line,", pad).unwrap();
                    writeln!(output, "{}        column: self.column,", pad).unwrap();
                    writeln!(
                        output,
                        "{}        message: \"Expected at least one match\",",
                        pad
                    )
                    .unwrap();
                    writeln!(output, "{}        expected: vec![],", pad).unwrap();
                    writeln!(output, "{}    }});", pad).unwrap();
                    writeln!(output, "{}}}", pad).unwrap();
                }
            }

            ExprKind::Group(inner) => {
                self.generate_expression(output, inner, indent)?;
            }

            ExprKind::Lookahead(inner, positive) => {
                writeln!(
                    output,
                    "{}// Lookahead ({})",
                    pad,
                    if *positive { "positive" } else { "negative" }
                )
                .unwrap();
                writeln!(output, "{}{{", pad).unwrap();
                writeln!(output, "{}    let saved_pos = self.position;", pad).unwrap();
                writeln!(
                    output,
                    "{}    let lookahead_result = self.parse_optional(|| {{",
                    pad
                )
                .unwrap();
                self.generate_expression(output, inner, indent + 2)?;
                writeln!(output, "{}        Ok(())", pad).unwrap();
                writeln!(output, "{}    }});", pad).unwrap();
                writeln!(output, "{}    self.position = saved_pos;", pad).unwrap();
                writeln!(output, "{}    if {} {{", pad, positive).unwrap();
                writeln!(output, "{}        if lookahead_result.is_err() {{", pad).unwrap();
                writeln!(output, "{}            return Err(ParseError {{ line: self.line, column: self.column, message: \"Lookahead failed\", expected: vec![] }});", pad).unwrap();
                writeln!(output, "{}        }}", pad).unwrap();
                writeln!(output, "{}    }} else {{", pad).unwrap();
                writeln!(output, "{}        if lookahead_result.is_ok() {{", pad).unwrap();
                writeln!(output, "{}            return Err(ParseError {{ line: self.line, column: self.column, message: \"Negative lookahead failed\", expected: vec![] }});", pad).unwrap();
                writeln!(output, "{}        }}", pad).unwrap();
                writeln!(output, "{}    }}", pad).unwrap();
                writeln!(output, "{}}}", pad).unwrap();
            }

            ExprKind::Regex(pattern) => {
                writeln!(output, "{}// Regex match: {}", pad, pattern).unwrap();
                writeln!(output, "{}{{", pad).unwrap();
                writeln!(
                    output,
                    "{}    let regex = regex::Regex::new(r#\"{}\"#).unwrap();",
                    pad, pattern
                )
                .unwrap();
                writeln!(
                    output,
                    "{}    let text: String = self.input[self.position..]",
                    pad
                )
                .unwrap();
                writeln!(output, "{}        .iter()", pad).unwrap();
                writeln!(
                    output,
                    "{}        .take_while(|&c| *c as u8 as char != '\\n')",
                    pad
                )
                .unwrap();
                writeln!(output, "{}        .map(|&c| c as u8 as char)", pad).unwrap();
                writeln!(output, "{}        .collect();", pad).unwrap();
                writeln!(output, "").unwrap();
                writeln!(output, "{}    if let Some(m) = regex.find(&text) {{", pad).unwrap();
                writeln!(output, "{}        let match_len = m.end();", pad).unwrap();
                writeln!(output, "{}        for _ in 0..match_len {{", pad).unwrap();
                writeln!(output, "{}            self.advance(1);", pad).unwrap();
                writeln!(output, "{}        }}", pad).unwrap();
                writeln!(output, "{}    }} else {{", pad).unwrap();
                writeln!(output, "{}        return Err(ParseError {{ line: self.line, column: self.column, message: \"Regex match failed\", expected: vec![\"{}\"] }});", pad, pattern).unwrap();
                writeln!(output, "{}    }}", pad).unwrap();
                writeln!(output, "{}}}", pad).unwrap();
            }

            ExprKind::Epsilon => {
                // Nada a fazer — sempre sucesso
            }

            ExprKind::Template(name, args) => {
                writeln!(output, "{}// Template: {}({:?})", pad, name, args).unwrap();
                writeln!(output, "{}// (Expandir para regras parametrizadas)", pad).unwrap();
            }
        }

        Ok(())
    }

    fn compute_rule_id(&self, name: &str) -> u32 {
        // Hash simples do nome da regra
        let mut hash: u32 = 2166136261;
        for c in name.bytes() {
            hash ^= c as u32;
            hash = hash.wrapping_mul(16777619);
        }
        hash
    }

    fn generate_ast(&self, output: &mut String) {
        writeln!(
            output,
            r#"
// ============================================================================
// AST TYPES
// ============================================================================

/// Nó da AST gerada pelo parser
#[derive(Clone, Debug, PartialEq)]
pub enum {}AST {{
    // Gerado automaticamente a partir das regras
"#,
            self.grammar.name.to_uppercase()
        )
        .unwrap();

        for (name, rule) in &self.grammar.rules {
            if rule.is_inline || rule.is_fragment {
                continue;
            }
            writeln!(
                output,
                "    /// Regra: {}\n    {}(Vec<{}AST>),",
                name,
                name,
                self.grammar.name.to_uppercase()
            )
            .unwrap();
        }

        writeln!(
            output,
            r#"}}
"#
        )
        .unwrap();
    }

    fn generate_utilities(&self, output: &mut String) {
        writeln!(
            output,
            r#"
// ============================================================================
// UTILIDADES
// ============================================================================

impl {}Parser {{
    /// Parse completo (entry point)
    pub fn parse(&mut self, start_rule: &str) -> ParseResult<()> {{
        match start_rule {{
"#,
            self.grammar.name.to_uppercase()
        )
        .unwrap();

        for (name, _) in &self.grammar.rules {
            if self.grammar.start_rules.contains(name) || self.grammar.start_rules.is_empty() {
                writeln!(
                    output,
                    r#"            "{}" => self.parse_rule_{}(),"#,
                    name,
                    name.replace("-", "_")
                )
                .unwrap();
            }
        }

        writeln!(
            output,
            r#"            _ => Err(ParseError {{
                line: self.line,
                column: self.column,
                message: "Unknown start rule",
                expected: vec![],
            }}),
        }}
    }}

    /// Verificar se parsing é possível a partir da posição atual
    fn parse_optional<F>(&mut self, mut f: F) -> ParseResult<()>
    where
        F: FnMut() -> ParseResult<()>,
    {{
        f()
    }}
}}

// ============================================================================
// ENTRY POINT
// ============================================================================

/// Parse de uma string usando a gramática compilada
pub fn parse(input: &str) -> ParseResult<()> {{
    let mut parser = {}Parser::new(input.as_bytes());
    if let Some(start_rule) = Some("{}") {{
        parser.parse(start_rule)
    }} else {{
        parser.parse("start")
    }}
}}
"#,
            self.grammar.name.to_uppercase(),
            self.grammar.name
        )
        .unwrap();
    }

    /// Salvar IR intermediário para debug
    #[allow(dead_code)]
    fn save_ir(_grammar: &LarkGrammar, path: &Path) -> Result<(), CompilerError> {
        let _ir_path = path.with_extension("ir.json");
        // let json = serde_json::to_string_pretty(grammar)
        //    .map_err(|e| CompilerError::GenerationError(e.to_string()))?;
        // fs::write(ir_path, json)
        //     .map_err(|e| CompilerError::Io(e))?;
        Ok(())
    }

    /// Salvar código Rust gerado
    pub fn save_rust_source(&self, path: &Path) -> Result<(), CompilerError> {
        let rust_source = self.compile()?;
        fs::write(path, rust_source).map_err(|e| CompilerError::Io(e))?;
        Ok(())
    }
}

// ============================================================================
// CLI TOOL
// ============================================================================

/// Compilar gramática Lark via linha de comando
pub fn compile_lark_cli(input_path: &str, output_path: &str) -> Result<(), CompilerError> {
    let input = Path::new(input_path);
    let output = Path::new(output_path);

    println!("Compilando gramática: {}", input.display());

    let rust_source = LarkToRustCompiler::compile_file(input, None)?;

    println!("Gerando: {}", output.display());
    fs::write(output, rust_source)?;

    println!("✓ Gramática compilada com sucesso!");
    Ok(())
}
