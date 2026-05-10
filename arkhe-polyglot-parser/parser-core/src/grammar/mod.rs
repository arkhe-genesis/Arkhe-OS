use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use petgraph::graph::DiGraph;
use bitflags::bitflags;

/// Representação de uma gramática formal
#[derive(Clone, Debug)]
pub struct Grammar {
    pub name: String,
    pub version: String,
    pub language_type: LanguageType,
    pub start_symbol: String,
    pub rules: HashMap<String, Vec<ProductionRule>>,
    pub terminals: Vec<TerminalDefinition>,
    pub precedence_table: PrecedenceTable,
    pub semantic_actions: HashMap<String, SemanticAction>,
}

/// Tipo de linguagem (para seleção de parser)
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum LanguageType {
    FreeForm,          // Forma livre (C, Java, Rust, etc.)
    IndentationSensitive, // Sensível a indentação (Python, Haskell)
    PatternBased,      // Baseado em padrões (Prolog, SQL)
    ExpressionBased,   // Baseado em expressões (Lisp, Clojure)
    Mixed,             // Combinação (Haskell = indent + free)
    Declarative,
}

/// Regra de produção
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct ProductionRule {
    pub lhs: String,                       // Lado esquerho (não-terminal)
    pub rhs: Vec<Symbol>,                  // Lado direito (símbolos)
    pub priority: u32,                     // Prioridade para conflitos
    pub action: Option<String>,            // Ação semântica (nome)
    pub documentation: Option<String>,     // Documentação da regra
}

/// Símbolo terminal ou não-terminal
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum Symbol {
    Terminal(String),
    NonTerminal(String),
    Epsilon,
    Wildcard,
}

/// Definição de terminal com expressão regular
#[derive(Clone, Debug)]
pub struct TerminalDefinition {
    pub name: String,
    pub pattern: String,                   // Regex
    pub flags: TerminalFlags,
}

bitflags! {
    #[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
    pub struct TerminalFlags: u32 {
        const CASE_SENSITIVE  = 0b00000001;
        const UNICODE_AWARE   = 0b00000010;
        const MULTILINE       = 0b00000100;
        const GREEDY          = 0b00001000;
    }
}

/// Tabela de precedência de operadores
#[derive(Clone, Debug, Default)]
pub struct PrecedenceTable {
    levels: Vec<PrecedenceLevel>,
}

#[derive(Clone, Debug)]
pub struct PrecedenceLevel {
    pub level: u32,
    pub associativity: Associativity,
    pub operators: Vec<String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Associativity {
    Left,
    Right,
    NonAssociative,
}

/// Ação semântica (executada durante a redução)
#[derive(Clone, Debug)]
pub struct SemanticAction {
    pub name: String,
    pub params: Vec<String>,
    pub code: String, // Pode ser Wasm bytecode ou nome de função
}

#[derive(Clone, Debug)]
pub struct LanguageSpec {
    pub name: String,
    pub display_name: String,
    pub version: String,
    pub language_type: LanguageType,
    pub author: String,
    pub description: String,
    pub file_extensions: Vec<String>,
    pub shebangs: Vec<String>,
    pub grammar_version: String,
}

pub struct GrammarPool {
    languages: HashMap<String, LanguageSpec>,
    total_languages: usize,
}

impl GrammarPool {
    pub fn new(_cache_enabled: bool) -> Self {
        Self {
            languages: HashMap::new(),
            total_languages: 0,
        }
    }

    pub fn register_defaults(&mut self) {
        let specs = vec![
            LanguageSpec {
                name: "rust".to_string(), display_name: "Rust".to_string(), version: "2024".to_string(), language_type: LanguageType::FreeForm, author: "Rust Team".to_string(), description: "Systems".to_string(), file_extensions: vec![".rs".into()], shebangs: vec![], grammar_version: "1.0".to_string(),
            },
            LanguageSpec {
                name: "python".to_string(), display_name: "Python".to_string(), version: "3.12".to_string(), language_type: LanguageType::IndentationSensitive, author: "PSF".to_string(), description: "Scripting".to_string(), file_extensions: vec![".py".into()], shebangs: vec![], grammar_version: "3.12".to_string(),
            },
            LanguageSpec {
                name: "javascript".to_string(), display_name: "JavaScript".to_string(), version: "ES2024".to_string(), language_type: LanguageType::FreeForm, author: "ECMA".to_string(), description: "Web".to_string(), file_extensions: vec![".js".into()], shebangs: vec![], grammar_version: "ES2024".to_string(),
            },
        ];

        for spec in specs {
            self.languages.insert(spec.name.clone(), spec);
            self.total_languages += 1;
        }
    }

    pub fn get_by_extension(&self, ext: &str) -> Option<&LanguageSpec> {
        let ext_lower = ext.to_lowercase();
        self.languages.values().find(|spec| spec.file_extensions.iter().any(|e| e.to_lowercase() == ext_lower || e.to_lowercase() == format!(".{}", ext_lower)))
    }

    pub fn detect(&self, filename: Option<&str>, content: &str) -> Option<(&LanguageSpec, f64)> {
        let mut candidates = Vec::new();

        if let Some(name) = filename {
            if let Some(ext) = std::path::Path::new(name).extension() {
                if let Some(spec) = self.get_by_extension(ext.to_str().unwrap_or("")) {
                    candidates.push((spec, 0.8));
                }
            }
        }

        for spec in self.languages.values() {
            let score = self.score_content_match(content, spec);
            if score > 0.3 {
                candidates.push((spec, score));
            }
        }

        candidates.into_iter().max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal))
    }

    fn score_content_match(&self, content: &str, spec: &LanguageSpec) -> f64 {
        let keywords = self.get_keywords_for_language(&spec.name);
        let mut hits = 0;
        let total = keywords.len();
        if total == 0 { return 0.0; }
        for kw in &keywords {
            if content.contains(kw) { hits += 1; }
        }
        (hits as f64 / total as f64).min(1.0)
    }

    fn get_keywords_for_language(&self, lang: &str) -> Vec<&'static str> {
        match lang {
            "rust" => vec!["fn ", "let mut", "impl", "trait", "struct", "enum"],
            "python" => vec!["def ", "class ", "import ", "from ", "as "],
            "javascript" => vec!["function ", "const ", "let ", "var "],
            _ => vec![],
        }
    }
}
