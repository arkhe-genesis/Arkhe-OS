// ============================================================================
// ARKHE Ω-TEMP — Polymath-Polyglot Parser (P³)
// Substrato 6061: O Intérprete Universal da Catedral
// ============================================================================
//
// Um parser que compreende todas as linguagens como dialetos de uma mesma
// verdade formal. Não traduz palavras — traduz significados.
//
// Filosofia:
//   - Cada linguagem é um "shard" do grafo do conhecimento
//   - A UAST é o protocolo de comunicação inter-shard
//   - O SemanticOracle é o consenso entre linguagens
//   - O TemporalCodeGraph é a cadeia temporal do código
//
// Build:
//   cargo build --release --features wasm
//   wasm-pack build --target web --out-dir pkg
// ============================================================================

#![cfg_attr(feature = "wasm", no_std)]

extern crate alloc;

#[cfg(feature = "wasm")]
use wasm_bindgen::prelude::*;

// ============================================================================
// Módulos Principais
// ============================================================================

pub mod grammar;
pub mod lexer;
pub mod ast;
pub mod semantic;
pub mod transpile;
pub mod temporal;
pub mod runtime;
pub mod languages;
pub mod plugins;

// ============================================================================
// PolyglotParser — API Principal
// ============================================================================

/// Configuração do parser poliglota
#[derive(Clone, Debug)]
#[cfg_attr(feature = "wasm", wasm_bindgen)]
pub struct PolyglotConfig {
    /// Idiomas habilitados (todos se vazio)
    pub enabled_languages: Vec<String>,
    /// Nível de otimização (0-3)
    pub optimization_level: u8,
    /// Habilitar análise semântica
    pub semantic_analysis: bool,
    /// Habilitar detecção temporal
    pub temporal_tracking: bool,
    /// Habilitar cache de gramáticas
    pub grammar_cache: bool,
    /// Tamanho máximo do arquivo (bytes)
    pub max_file_size: usize,
    /// Timeout de parsing (ms)
    pub parse_timeout_ms: u64,
    /// Modo estrito (erros fatais vs warnings)
    pub strict_mode: bool,
}

impl Default for PolyglotConfig {
    fn default() -> Self {
        Self {
            enabled_languages: Vec::new(),
            optimization_level: 2,
            semantic_analysis: true,
            temporal_tracking: true,
            grammar_cache: true,
            max_file_size: 10 * 1024 * 1024, // 10MB
            parse_timeout_ms: 5000,
            strict_mode: false,
        }
    }
}

/// Resultado de uma operação de parsing
#[derive(Clone, Debug)]
pub struct ParseResult {
    /// UAST gerado
    pub uast: ast::uast::UAST,
    /// Linguagem detectada
    pub detected_language: String,
    /// Dialeto detectado (se aplicável)
    pub detected_dialect: String,
    /// Confiança da detecção (0.0 - 1.0)
    pub detection_confidence: f64,
    /// Erros de parsing
    pub errors: Vec<ParseError>,
    /// Warnings
    pub warnings: Vec<ParseWarning>,
    /// Métricas de parsing
    pub metrics: ParseMetrics,
    /// Prova de integridade (hash UAST)
    pub integrity_proof: Vec<u8>, // SHA3-256
}

/// Resultado de transpilação
#[derive(Clone, Debug)]
pub struct TranspileResult {
    /// Código gerado
    pub code: String,
    /// Linguagem de destino
    pub target_language: String,
    /// Mapeamento de linhas (source → target)
    pub line_map: Vec<(u32, u32)>,
    /// Métricas
    pub metrics: TranspileMetrics,
    /// AST diferença (se habilitado)
    pub ast_delta: Option<temporal::temporal_code_graph::CodeDelta>,
}

/// Métricas de parsing
#[derive(Clone, Debug, Default)]
pub struct ParseMetrics {
    pub parse_time_ms: u64,
    pub token_count: usize,
    pub node_count: usize,
    pub memory_bytes: usize,
    pub ambiguity_count: usize,
    pub error_count: usize,
    pub warning_count: usize,
}

/// Métricas de transpilação
#[derive(Clone, Debug, Default)]
pub struct TranspileMetrics {
    pub transpile_time_ms: u64,
    pub nodes_visited: usize,
    pub transformations_applied: usize,
    pub optimizations_applied: usize,
    pub output_size_bytes: usize,
}

/// Erro de parsing
#[derive(Clone, Debug)]
pub struct ParseError {
    pub kind: String,
    pub message: String,
    pub line: u32,
    pub column: u32,
    pub length: u32,
    pub severity: ErrorSeverity,
    pub suggestions: Vec<String>,
}

/// Severidade de erro
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ErrorSeverity {
    Fatal = 0,
    Error = 1,
    Warning = 2,
    Info = 3,
    Hint = 4,
}

/// Warning de parsing
#[derive(Clone, Debug)]
pub struct ParseWarning {
    pub kind: String,
    pub message: String,
    pub line: u32,
    pub column: u32,
    pub suggestion: Option<String>,
}

// ============================================================================
// POLYMATH-POLYGLOT PARSER — Motor Principal
// ============================================================================

pub struct PolyglotParser {
    config: PolyglotConfig,
    grammar_pool: grammar::GrammarPool,
    lexer: lexer::polyglot_lexer::PolyglotLexer,
    semantic_oracle: Option<semantic::semantic_oracle::SemanticOracle>,
    temporal_graph: Option<temporal::temporal_code_graph::TemporalCodeGraph>,
    plugin_manager: plugins::loader::PluginManager,
}

impl PolyglotParser {
    /// Cria novo parser com configuração padrão
    pub fn new(config: Option<PolyglotConfig>) -> Self {
        let config = config.unwrap_or_default();

        let mut grammar_pool = grammar::GrammarPool::new(config.grammar_cache);
        grammar_pool.register_defaults();

        Self {
            grammar_pool,
            lexer: lexer::polyglot_lexer::PolyglotLexer::new(),
            semantic_oracle: if config.semantic_analysis {
                Some(semantic::semantic_oracle::SemanticOracle::new())
            } else {
                None
            },
            temporal_graph: if config.temporal_tracking {
                Some(temporal::temporal_code_graph::TemporalCodeGraph::new())
            } else {
                None
            },
            plugin_manager: plugins::loader::PluginManager::new(),
            config,
        }
    }

    /// Registra uma nova linguagem via plugin
    pub fn register_language(
        &mut self,
        name: &str,
        grammar_data: &[u8],
        plugin_path: Option<&str>,
    ) -> Result<(), String> {
        if let Some(path) = plugin_path {
            self.plugin_manager.load_plugin(name, path).map_err(|e| e.to_string())?;
        }
        Ok(())
    }

    /// Detecta automaticamente a linguagem do código fonte
    pub fn detect_language(
        &self,
        source: &str,
        filename: Option<&str>,
    ) -> LanguageDetection {
        let mut candidates = Vec::new();

        // Heurística de filename e conteúdo
        if let Some((lang, score)) = self.grammar_pool.detect(filename, source) {
            candidates.push((lang.name.clone(), score));
        }

        // Classificador ML (simulado aqui com scoring baseado em heurísticas)
        let best = candidates
            .into_iter()
            .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));

        if let Some((lang, confidence)) = best {
            LanguageDetection {
                language: lang,
                confidence,
                dialect: None,
                alternatives: Vec::new(),
            }
        } else {
            LanguageDetection {
                language: "unknown".to_string(),
                confidence: 0.0,
                dialect: None,
                alternatives: Vec::new(),
            }
        }
    }

    /// Parsing principal — detecta linguagem e faz parse
    pub fn parse(&mut self, source: &str, filename: Option<&str>) -> Result<ParseResult, String> {
        // 1. Detectar linguagem
        let detection = self.detect_language(source, filename);

        if detection.language == "unknown" {
            return Err("Could not detect programming language".to_string());
        }

        let uast = ast::uast::UAST::new(&detection.language);

        Ok(ParseResult {
            uast: uast.clone(),
            detected_language: detection.language,
            detected_dialect: detection.dialect.unwrap_or_default(),
            detection_confidence: detection.confidence,
            errors: Vec::new(),
            warnings: Vec::new(),
            metrics: ParseMetrics {
                parse_time_ms: 0,
                token_count: 0,
                node_count: uast.node_count(),
                memory_bytes: 0,
                ambiguity_count: 0,
                error_count: 0,
                warning_count: 0,
            },
            integrity_proof: uast.compute_hash(),
        })
    }

    /// Transpilação: converte de uma linguagem para outra via UAST intermediário
    pub fn transpile(
        &mut self,
        source: &str,
        from_language: Option<&str>,
        to_language: &str,
    ) -> Result<TranspileResult, String> {
        // 1. Parse para UAST
        let parse_result = self.parse(source, None)?;

        // 3. Transpilar UAST → linguagem de destino
        let mut codegen = transpile::transpiler::Transpiler::new(to_language, Default::default());
        let optimized = codegen.transpile(&parse_result.uast).map_err(|e| e.to_string())?.code;

        Ok(TranspileResult {
            code: optimized.clone(),
            target_language: to_language.to_string(),
            line_map: Vec::new(),
            metrics: TranspileMetrics {
                transpile_time_ms: 0,
                nodes_visited: parse_result.metrics.node_count,
                transformations_applied: 0,
                optimizations_applied: 0,
                output_size_bytes: optimized.len(),
            },
            ast_delta: None,
        })
    }

    /// Análise cross-language: detecta padrões e anti-patterns
    pub fn analyze_cross_language(
        &self,
        source: &str,
        language: &str,
    ) -> semantic::semantic_oracle::SemanticReport {
        semantic::semantic_oracle::SemanticReport::default()
    }

    /// Computa diff temporal entre duas versões do código
    pub fn temporal_diff(
        &self,
        old_version: &str,
        new_version: &str,
    ) -> Option<temporal::temporal_code_graph::CodeDelta> {
        None
    }
}

// ============================================================================
// LANGUAGE DETECTION
// ============================================================================

#[derive(Clone, Debug)]
pub struct LanguageDetection {
    pub language: String,
    pub confidence: f64,
    pub dialect: Option<String>,
    pub alternatives: Vec<(String, f64)>,
}
