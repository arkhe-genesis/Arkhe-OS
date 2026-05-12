// ============================================================================
// ARKHE P³ — Polyglot Lexer
// ============================================================================
// Lexer adaptativo que auto-detecta o idioma e ajusta tokenização em tempo real.
// Usa DFA compilado dinamicamente a partir das gramáticas registradas.
// ============================================================================

use crate::grammar::{Grammar, TerminalDefinition, TerminalFlags};
use crate::lexer::token::{Token, TokenKind, TokenSpan};
use ahash::AHashMap;
use regex::bytes::Regex as BytesRegex;
use unicode_segmentation::UnicodeSegmentation;

/// Estado do DFA do lexer
#[derive(Clone, Debug)]
struct DfaState {
    transitions: AHashMap<u8, usize>, // byte → próximo estado
    accept: Option<TokenKind>,        // Token aceito neste estado
    fallback: usize,                  // Estado de fallback
}

/// Lexer poliglota — tokeniza qualquer linguagem registrada
pub struct PolyglotLexer {
    dfas: AHashMap<String, Vec<DfaState>>, // language → DFA states
    combined_dfa: Option<Vec<DfaState>>,   // DFA combinado (todos os idiomas)
    buffer: Vec<u8>,
    position: usize,
    line: u32,
    column: u32,
    language_hint: Option<String>,
}

impl PolyglotLexer {
    /// Cria novo lexer vazio
    pub fn new() -> Self {
        Self {
            dfas: AHashMap::new(),
            combined_dfa: None,
            buffer: Vec::new(),
            position: 0,
            line: 1,
            column: 1,
            language_hint: None,
        }
    }

    /// Tokeniza source em uma linguagem específica
    pub fn tokenize(
        &mut self,
        source: &str,
        grammar: &Grammar,
    ) -> Result<Vec<Token>, LexerError> {
        // Compilar DFA se necessário
        let lang = &grammar.name;
        if !self.dfas.contains_key(lang) {
            self.compile_dfa(grammar)?;
        }

        self.buffer = source.as_bytes().to_vec();
        self.position = 0;
        self.line = 1;
        self.column = 1;
        self.language_hint = Some(lang.clone());

        let mut tokens = Vec::new();

        while self.position < self.buffer.len() {
            // Pular whitespace/comments
            self.skip_whitespace(source);
            self.skip_comments(source, grammar)?;

            if self.position >= self.buffer.len() {
                break;
            }

            // Tentar tokenizar usando o DFA
            match self.scan_token(source, grammar) {
                Ok(Some(token)) => {
                    tokens.push(token);
                }
                Ok(None) => {
                    // Nenhum token reconhecido — erro ou fallback
                    if grammar.language_type == crate::grammar::LanguageType::FreeForm {
                        // Em linguagem de forma livre, tentar single-char fallback
                        let ch = self.buffer[self.position];
                        tokens.push(Token::new(
                            TokenKind::Unknown(ch as char),
                            self.line,
                            self.column,
                            1,
                        ));
                        self.advance(1);
                    } else {
                        return Err(LexerError::UnexpectedCharacter {
                            found: self.buffer[self.position] as char,
                            line: self.line,
                            column: self.column,
                        });
                    }
                }
                Err(e) => return Err(e),
            }
        }

        tokens.push(Token::new(TokenKind::Eof, self.line, self.column, 0));
        Ok(tokens)
    }

    /// Compilar DFA a partir da gramática
    fn compile_dfa(&mut self, grammar: &Grammar) -> Result<(), LexerError> {
        let mut states: Vec<DfaState> = vec![DfaState {
            transitions: AHashMap::new(),
            accept: None,
            fallback: 0,
        }];

        // Para cada terminal, adicionar ao DFA
        for terminal in &grammar.terminals {
            let regex = regex::Regex::new(&terminal.pattern)
                .map_err(|e| LexerError::InvalidRegex {
                    pattern: terminal.pattern.clone(),
                    error: e.to_string(),
                })?;

            // Nesta implementação simplificada, usamos regex matching
            // Em produção: compilar para AFA/DFA verdadeiro
            // ...
        }

        self.dfas.insert(grammar.name.clone(), states);
        self.rebuild_combined_dfa();

        Ok(())
    }

    /// Reconstruir DFA combinado para detecção multi-linguagem
    fn rebuild_combined_dfa(&mut self) {
        // Na implementação completa, combina todos os DFAs
        // em um único autômato com marcação de idioma
        self.combined_dfa = None; // Placeholder — implementação pesada
    }

    /// Scan de um único token
    fn scan_token(
        &mut self,
        source: &str,
        grammar: &Grammar,
    ) -> Result<Option<Token>, LexerError> {
        let dfa = self.dfas.get(&grammar.name).unwrap();
        let mut state = 0usize;
        let mut last_accept = None;
        let mut last_accept_pos = self.position;
        let mut current_pos = self.position;

        while current_pos <= self.buffer.len() {
            let dfa_state = &dfa[state];

            if let Some(token_kind) = &dfa_state.accept {
                last_accept = Some(token_kind.clone());
                last_accept_pos = current_pos;
            }

            if current_pos >= self.buffer.len() {
                break;
            }

            let byte = self.buffer[current_pos];

            if let Some(&next_state) = dfa_state.transitions.get(&byte) {
                state = next_state;
                current_pos += 1;
            } else {
                break;
            }
        }

        if let Some(token_kind) = last_accept {
            let token_len = last_accept_pos - self.position;
            let token_str = &source[self.position..last_accept_pos];

            // Aplicar flags do terminal (case sensitivity, etc.)
            let actual_kind = self.resolve_token_kind(token_kind, token_str, grammar);

            let token = Token::new(
                actual_kind,
                self.line,
                self.column,
                token_len,
            );

            self.advance(token_len);
            Ok(Some(token))
        } else if current_pos > self.position {
            // Progresso parcial — tentar longest match
            self.advance(1);
            Ok(None)
        } else {
            Ok(None)
        }
    }

    /// Resolver tipo de token com base em flags e contexto
    fn resolve_token_kind(
        &self,
        kind: TokenKind,
        text: &str,
        grammar: &Grammar,
    ) -> TokenKind {
        // Em linguagens sensíveis a contexto (ex: Python),
        // verificar indentação
        if grammar.language_type == crate::grammar::LanguageType::IndentationSensitive {
            return self.resolve_indentation_token(kind, text, grammar);
        }

        // Verificar palavras-chave contextuais
        // (ex: "async" pode ser keyword ou identifier dependendo do contexto)
        if let TokenKind::Identifier = kind {
            if grammar.terminals.iter().any(|t| t.name == text) {
                // Pesquisar se é keyword
                // ...
            }
        }

        kind
    }

    /// Resolver tokens de indentação (Python, Haskell, etc.)
    fn resolve_indentation_token(
        &self,
        kind: TokenKind,
        text: &str,
        grammar: &Grammar,
    ) -> TokenKind {
        // Rastrear nível de indentação
        // ...
        kind
    }

    /// Pular whitespace
    fn skip_whitespace(&mut self, source: &str) {
        while self.position < self.buffer.len() {
            let byte = self.buffer[self.position];
            match byte {
                b' ' | b'\t' | b'\r' => {
                    self.advance(1);
                }
                b'\n' => {
                    self.line += 1;
                    self.column = 1;
                    self.advance(1);
                }
                _ => break,
            }
        }
    }

    /// Pular comentários (detecção multi-linguagem)
    fn skip_comments(
        &mut self,
        source: &str,
        grammar: &Grammar,
    ) -> Result<(), LexerError> {
        // Determinar estilo de comentário baseado na gramática
        // (Implementado com matching de padrão)
        // ...
        Ok(())
    }

    /// Detectar idioma automaticamente via análise léxica
    pub fn detect_language(
        &self,
        source: &str,
        available_grammars: &[&Grammar],
    ) -> Vec<(String, f64)> {
        let mut scores: Vec<(String, f64)> = Vec::new();

        for grammar in available_grammars {
            let score = self.score_grammar_match(source, grammar);
            if score > 0.01 {
                scores.push((grammar.name.clone(), score));
            }
        }

        scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        scores
    }

    /// Score de correspondência entre source e gramática
    fn score_grammar_match(&self, source: &str, grammar: &Grammar) -> f64 {
        let tokens = self.quick_scan(source);
        let mut score = 0.0;
        let mut matched = 0;
        let mut total = 0;

        for token_str in &tokens {
            total += 1;
            // Verificar se token é reconhecível nesta gramática
            for terminal in &grammar.terminals {
                let re = regex::Regex::new(&terminal.pattern).unwrap();
                if re.is_match(token_str) {
                    matched += 1;
                    // Keywords valem mais que identifiers
                    if terminal.name.starts_with("KW_") {
                        score += 3.0;
                    } else {
                        score += 1.0;
                    }
                    break;
                }
            }
        }

        if total == 0 {
            return 0.0;
        }

        // Normalizar
        score / (total as f64)
    }

    /// Scan rápido para detecção de idioma
    fn quick_scan(&self, source: &str) -> Vec<String> {
        source.split(|c: char| !c.is_alphanumeric() && c != '_')
            .filter(|s| !s.is_empty() && s.len() <= 50)
            .take(500) // Limitar para performance
            .map(String::from)
            .collect()
    }

    fn advance(&mut self, n: usize) {
        for _ in 0..n {
            if self.position < self.buffer.len() {
                let byte = self.buffer[self.position];
                if byte == b'\n' {
                    self.line += 1;
                    self.column = 1;
                } else {
                    self.column += 1;
                }
                self.position += 1;
            }
        }
    }
}

// ============================================================================
// TOKEN DEFINITION
// ============================================================================

pub mod token {
    // use super::TokenKind;

    #[derive(Clone, Debug, PartialEq, Eq, Hash)]
    pub struct Token {
        pub kind: TokenKind,
        pub line: u32,
        pub column: u32,
        pub length: usize,
        pub text: String, // Populado durante scan
    }

    impl Token {
        pub fn new(kind: TokenKind, line: u32, column: u32, length: usize) -> Self {
            Self {
                kind,
                line,
                column,
                length,
                text: String::new(),
            }
        }
    }

    /// Enum abrangente de tipos de token — compartilhado entre todas as linguagens
    /// Usa um sistema de classificação hierárquica
    #[derive(Clone, Debug, PartialEq, Eq, Hash)]
    pub enum TokenKind {
        // ===== Palavras-chave universais por categoria =====

        // Controle de fluxo
        KwIf,
        KwElse,
        KwWhile,
        KwFor,
        KwLoop,
        KwMatch,
        KwSwitch,
        KwCase,
        KwDefault,
        KwBreak,
        KwContinue,
        KwReturn,
        KwThrow,
        KwTry,
        KwCatch,
        KwFinally,
        KwYield,
        KwAwait,
        KwAsync,
        KwGoto,

        // Tipos
        KwType,       // type, typename, typedef
        KwStruct,
        KwEnum,
        KwClass,
        KwTrait,
        KwInterface,
        KwProtocol,
        KwImpl,       // impl, implements
        KwFn,         // fn, func, function, def, lambda
        KwVar,        // var, mut, let, const, val
        KwVoid,
        KwNull,
        KwTrue,
        KwFalse,
        KwSelf,       // self, this
        KwSuper,

        // Módulos
        KwImport,
        KwExport,
        KwModule,
        KwPackage,
        KwUse,
        KwPub,        // pub, public, private

        // Controle de concorrência
        KwSpawn,
        KwThread,
        KwChannel,
        KwLock,
        KwMutex,
        KwAtomic,

        // Operadores
        OpArithPlus,
        OpArithMinus,
        OpArithMul,
        OpArithDiv,
        OpArithMod,
        OpArithPow,
        OpAssign,
        OpAssignAdd,
        OpAssignSub,
        OpAssignMul,
        OpAssignDiv,
        OpCompareEq,
        OpCompareNeq,
        OpCompareLt,
        OpCompareGt,
        OpCompareLte,
        OpCompareGte,
        OpLogicAnd,
        OpLogicOr,
        OpLogicNot,
        OpBitAnd,
        OpBitOr,
        OpBitXor,
        OpBitNot,
        OpShiftL,
        OpShiftR,
        OpArrow,         // ->, =>, :, ::=
        OpPipe,          // |, |>, >>
        OpRange,         // .., ...
        OpSpread,        // ...
        OpTernary,       // ?
        OpNullCoalesce,  // ??
        OpOptional,      // ?.
        OpRest,          // ...

        // Delimitadores
        DelLParen,       // (
        DelRParen,       // )
        DelLBracket,     // [
        DelRBracket,     // ]
        DelLBrace,       // {
        DelRBrace,       // }
        DelComma,        // ,
        DelSemicolon,    // ;
        DelColon,        // :
        DelDot,          // .
        DelDotDot,       // ..
        DelPipe,         // |
        DelBacktick,     // `
        DelHash,         // #
        DelAt,           // @
        DelDollar,       // $
        DelQuestion,     // ?
        DelBang,         // !
        DelAmp,          // &
        DelPercent,      // %
        DelCaret,        // ^
        DelTilde,        // ~

        // Literais
        LitInteger,       // 42, 0xFF, 0b1010, 0o77
        LitFloat,         // 3.14, 1.0e10
        LitString,        // "hello", 'world'
        LitChar,          // 'a', '\n'
        LitBool,          // true, false
        LitNull,          // null, None, nil
        LitUndefined,     // undefined
        LitThis,          // this, self

        // Identificadores
        Identifier,
        TypeIdentifier,
        Label,

        // Comentários
        CommentLine,
        CommentBlock,
        DocComment,

        // Meta
        MetaAnnotation,   // @, #[], decorator
        MetaAttribute,
        MetaDirective,     // #include, #pragma


        // Unknown
        Unknown(char),

        // EOF
        Eof,
    }

    impl TokenKind {
        /// Verifica se é keyword
        pub fn is_keyword(&self) -> bool {
            matches!(self, TokenKind::KwIf | TokenKind::KwElse) // TODO: expand
        }

        /// Verifica se é operador
        pub fn is_operator(&self) -> bool {
            matches!(self, TokenKind::OpArithPlus) // TODO: expand
        }

        /// Verifica se é delimitador
        pub fn is_delimiter(&self) -> bool {
            matches!(self, TokenKind::DelLParen) // TODO: expand
        }

        /// Verifica se é literal
        pub fn is_literal(&self) -> bool {
            matches!(self, TokenKind::LitInteger) // TODO: expand
        }

        /// Categoria do token
        pub fn category(&self) -> TokenCategory {
            match self {
                TokenKind::KwIf | TokenKind::KwElse | TokenKind::KwWhile => TokenCategory::Keyword,
                TokenKind::OpArithPlus => TokenCategory::Operator,
                TokenKind::DelLParen => TokenCategory::Delimiter,
                TokenKind::LitInteger => TokenCategory::Literal,
                TokenKind::Identifier => TokenCategory::Identifier,
                TokenKind::CommentLine | TokenKind::CommentBlock => TokenCategory::Comment,
                _ => TokenCategory::Other,
            }
        }

        /// Representação textual
        pub fn to_str(&self) -> &'static str {
            match self {
                TokenKind::KwIf => "if",
                TokenKind::KwElse => "else",
                TokenKind::KwWhile => "while",
                TokenKind::KwFor => "for",
                TokenKind::KwMatch => "match",
                TokenKind::KwReturn => "return",
                TokenKind::KwFn => "fn",
                TokenKind::KwLet => "let",
                TokenKind::KwMut => "mut",
                TokenKind::KwStruct => "struct",
                TokenKind::KwEnum => "enum",
                TokenKind::KwTrait => "trait",
                TokenKind::KwImpl => "impl",
                TokenKind::KwImport => "import",
                TokenKind::KwExport => "export",
                TokenKind::KwTrue => "true",
                TokenKind::KwFalse => "false",
                TokenKind::KwSelf => "self",
                TokenKind::KwNull => "null",
                TokenKind::KwNone => "None",
                TokenKind::LitInteger => "integer",
                TokenKind::LitFloat => "float",
                TokenKind::LitString => "string",
                TokenKind::LitChar => "char",
                TokenKind::LitBool => "bool",
                TokenKind::Identifier => "identifier",
                TokenKind::TypeIdentifier => "type_identifier",
                TokenKind::CommentLine => "//",
                TokenKind::CommentBlock => "/* */",
                TokenKind::Eof => "EOF",
                _ => "(other)",
            }
        }
    }

    #[derive(Clone, Debug, PartialEq, Eq, Hash)]
    pub enum TokenCategory {
        Keyword,
        Operator,
        Delimiter,
        Literal,
        Identifier,
        Comment,
        Annotation,
        Whitespace,
        Other,
    }

    #[derive(Clone, Debug)]
    pub struct TokenSpan {
        pub start: usize,
        pub end: usize,
        pub line: u32,
        pub column: u32,
    }
}

#[derive(Debug, thiserror::Error)]
pub enum LexerError {
    #[error("Tokenização interrompida: {reason}")]
    Interrupted { reason: String },

    #[error("Caractere inesperado '{found}' em {line}:{column}")]
    UnexpectedCharacter { found: char, line: u32, column: u32 },

    #[error("Sequência inválida em {line}:{column}")]
    InvalidSequence { line: u32, column: u32 },

    #[error("String não terminada em {line}:{column}")]
    UnterminatedString { line: u32, column: u32 },

    #[error("Comentário não terminado em {line}:{column}")]
    UnterminatedComment { line: u32, column: u32 },

    #[error("Número mal formado em {line}:{column}")]
    MalformedNumber { line: u32, column: u32 },

    #[error("Regex inválida: {pattern}: {error}")]
    InvalidRegex { pattern: String, error: String },

    #[error("Buffer overflow em {line}:{column}")]
    BufferOverflow { line: u32, column: u32 },
}
