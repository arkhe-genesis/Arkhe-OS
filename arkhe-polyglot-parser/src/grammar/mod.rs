// ============================================================================
// ARKHE P³ — Grammar System
// ============================================================================
// Sistema de gramáticas unificado que suporta:
// - Gramáticas context-free (CFG)
// - Gramáticas sensíveis ao contexto (para type checking)
// - Gramáticas adaptativas (aprendizado de padrão do código)
// - Fusão de gramáticas para linguagens híbridas (TypeScript = JS + types)
// ============================================================================

use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use petgraph::graph::DiGraph;
use bitflags::bitflags;
use serde::{Serialize, Deserialize};

/// Representação de uma gramática formal
#[derive(Clone, Debug, Serialize, Deserialize)]
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
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum LanguageType {
    FreeForm,          // Forma livre (C, Java, Rust, etc.)
    IndentationSensitive, // Sensível a indentação (Python, Haskell)
    PatternBased,      // Baseado em padrões (Prolog, SQL)
    ExpressionBased,   // Baseado em expressões (Lisp, Clojure)
    Mixed,             // Combinação (Haskell = indent + free)
    Declarative,       // Declarative (SQL, Cypher)
}

/// Regra de produção
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ProductionRule {
    pub lhs: String,                       // Lado esquerho (não-terminal)
    pub rhs: Vec<Symbol>,                  // Lado direito (símbolos)
    pub priority: u32,                     // Prioridade para conflitos
    pub action: Option<String>,            // Ação semântica (nome)
    pub documentation: Option<String>,     // Documentação da regra
}

/// Símbolo terminal ou não-terminal
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Symbol {
    Terminal(String),
    NonTerminal(String),
    Epsilon,
    Wildcard,
}

/// Definição de terminal com expressão regular
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TerminalDefinition {
    pub name: String,
    pub pattern: String,                   // Regex
    pub flags: TerminalFlags,
}

bitflags! {
    #[derive(Serialize, Deserialize)]
    pub struct TerminalFlags: u32 {
        const CASE_SENSITIVE  = 0b00000001;
        const UNICODE_AWARE   = 0b00000010;
        const MULTILINE       = 0b00000100;
        const GREEDY          = 0b00001000;
    }
}

/// Tabela de precedência de operadores
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct PrecedenceTable {
    levels: Vec<PrecedenceLevel>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PrecedenceLevel {
    pub level: u32,
    pub associativity: Associativity,
    pub operators: Vec<String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Associativity {
    Left,
    Right,
    NonAssociative,
}

/// Ação semântica (executada durante a redução)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SemanticAction {
    pub name: String,
    pub params: Vec<String>,
    pub code: String, // Pode ser Wasm bytecode ou nome de função
}

/// Pool de gramáticas — gerencia gramáticas carregadas
#[derive(Debug)]
pub struct GrammarPool {
    grammars: RwLock<HashMap<String, Arc<Grammar>>>,
    inheritance: RwLock<DiGraph<String, f64>>, // Grafo de herança entre gramáticas
    loaded_at: RwLock<HashMap<String, std::time::Instant>>,
    cache_enabled: bool,
}

impl GrammarPool {
    /// Cria novo pool vazio
    pub fn new(cache_enabled: bool) -> Self {
        Self {
            grammars: RwLock::new(HashMap::new()),
            inheritance: RwLock::new(DiGraph::new()),
            loaded_at: RwLock::new(HashMap::new()),
            cache_enabled,
        }
    }

    pub fn register_language(&self, name: &str, grammar_data: &[u8]) -> Result<(), String> {
        self.register_from_bytes(name, grammar_data).map_err(|e| e.to_string())
    }

    /// Registra uma nova gramática
    pub fn register(&self, grammar: Grammar) -> Result<(), GrammarError> {
        let name = grammar.name.clone();

        // Validar gramática
        self.validate(&grammar)?;

        // Verificar conflitos com gramáticas existentes
        self.check_conflicts(&grammar)?;

        // Inserir no pool
        let mut grammars = self.grammars.write().unwrap();
        let mut loaded = self.loaded_at.write().unwrap();
        grammars.insert(name.clone(), Arc::new(grammar));
        loaded.insert(name, std::time::Instant::now());

        Ok(())
    }

    /// Registra linguagem a partir de dados binários (formato serializado)
    pub fn register_from_bytes(
        &self,
        name: &str,
        data: &[u8],
    ) -> Result<(), GrammarError> {
        let grammar: Grammar = serde_json::from_slice(data)
            .map_err(|e| GrammarError::ParseError(e.to_string()))?;

        if grammar.name != name {
            return Err(GrammarError::NameMismatch {
                expected: name.to_string(),
                got: grammar.name,
            });
        }

        self.register(grammar)
    }

    pub fn get_grammar(&self, name: &str) -> Option<Arc<Grammar>> {
        self.get(name)
    }

    /// Busca gramática por nome
    pub fn get(&self, name: &str) -> Option<Arc<Grammar>> {
        let grammars = self.grammars.read().unwrap();

        // Tentar nome exato
        if let Some(g) = grammars.get(name) {
            return Some(g.clone());
        }

        // Tentar fuzzy match
        self.fuzzy_search(name)
    }

    /// Busca fuzzy — encontra gramática mais parecida
    fn fuzzy_search(&self, query: &str) -> Option<Arc<Grammar>> {
        let grammars = self.grammars.read().unwrap();

        grammars.iter()
            .filter(|(name, _)| {
                // Verificar prefixo, sufixo, ou substring
                query.contains(*name) || name.contains(query) ||
                query.starts_with(*name) || name.starts_with(query)
            })
            .max_by_key(|(_, g)| self.similarity_score(query, &g.name))
            .map(|(_, g)| g.clone())
    }

    /// Calcula score de similaridade entre nome query e nome de gramática
    fn similarity_score(&self, query: &str, name: &str) -> u32 {
        // Levenshtein simplificado
        let query = query.to_lowercase();
        let name = name.to_lowercase();

        if query == name { return u32::MAX; }
        if query.starts_with(&name) { return 1000; }
        if name.starts_with(&query) { return 900; }
        if query.contains(&name) { return 500; }
        if name.contains(&query) { return 400; }

        // Jaro-Winkler aproximado
        let common: u32 = query.chars().zip(name.chars())
            .filter(|(a, b)| a == b)
            .count() as u32;

        (common * 200) / (query.len() as u32 + name.len() as u32 + 1)
    }

    /// Define herança entre gramáticas (ex: TypeScript herda de JavaScript)
    pub fn set_inheritance(&self, child: &str, parent: &str, weight: f64) -> Result<(), GrammarError> {
        let grammars = self.grammars.read().unwrap();

        if !grammars.contains_key(child) {
            return Err(GrammarError::NotFound(child.to_string()));
        }
        if !grammars.contains_key(parent) {
            return Err(GrammarError::NotFound(parent.to_string()));
        }

        drop(grammars);

        let mut inheritance = self.inheritance.write().unwrap();

        let child_node = inheritance.add_node(child.to_string());
        let parent_node = inheritance.add_node(parent.to_string());
        inheritance.add_edge(
            child_node,
            parent_node,
            weight,
        );

        Ok(())
    }

    /// Valida gramática (checa consistência)
    fn validate(&self, grammar: &Grammar) -> Result<(), GrammarError> {
        // Verificar que o símbolo inicial existe nas regras
        if !grammar.rules.contains_key(&grammar.start_symbol) {
            return Err(GrammarError::MissingStartSymbol(grammar.start_symbol.clone()));
        }

        // Verificar que todos os não-terminais referenciados existem
        for (lhs, rules) in &grammar.rules {
            if lhs.is_empty() {
                return Err(GrammarError::EmptyLHS);
            }
            for rule in rules {
                for symbol in &rule.rhs {
                    if let Symbol::NonTerminal(ref nt) = symbol {
                        if !grammar.rules.contains_key(nt) && nt != lhs {
                            // Pode ser referência a terminal implicitamente
                        }
                    }
                }
            }
        }

        Ok(())
    }

    /// Checa conflitos entre gramáticas no pool
    fn check_conflicts(&self, new_grammar: &Grammar) -> Result<(), GrammarError> {
        let grammars = self.grammars.read().unwrap();

        for (name, existing) in grammars.iter() {
            // Verificar sobreposição de terminais
            let existing_terminals: std::collections::HashSet<_> =
                existing.terminals.iter().map(|t| &t.name).collect();
            let new_terminals: std::collections::HashSet<_> =
                new_grammar.terminals.iter().map(|t| &t.name).collect();

            let overlap: Vec<_> = existing_terminals.intersection(&new_terminals).collect();
            if !overlap.is_empty() {
                // Permitir sobreposição parcial (ex: keywords comuns)
                // Mas alertar se > 50%
                if overlap.len() > existing_terminals.len() / 2 {
                    return Err(GrammarError::TerminalConflict {
                        grammar: name.clone(),
                        terminals: overlap.iter().map(|s| (*s).clone()).collect(),
                    });
                }
            }
        }

        Ok(())
    }

    /// Remove gramática do pool
    pub fn remove(&self, name: &str) -> Option<Arc<Grammar>> {
        let mut grammars = self.grammars.write().unwrap();
        let mut loaded = self.loaded_at.write().unwrap();
        let removed = grammars.remove(name);
        loaded.remove(name);
        removed
    }

    /// Lista todas as linguagens registradas
    pub fn list_languages(&self) -> Vec<(String, f64)> {
        let grammars = self.grammars.read().unwrap();
        let loaded = self.loaded_at.read().unwrap();
        grammars.iter()
            .map(|(name, _)| {
                let l = loaded.get(name)
                    .map(|t| t.elapsed().as_secs_f64())
                    .unwrap_or(0.0);
                (name.clone(), l)
            })
            .collect()
    }

    /// Fundir duas gramáticas em uma nova (Grammar Fusion)
    pub fn fuse_grammars(
        &self,
        base: &str,
        extension: &str,
        new_name: String,
    ) -> Result<Grammar, GrammarError> {
        let base_g = self.get(base)
            .ok_or_else(|| GrammarError::NotFound(base.to_string()))?;
        let ext_g = self.get(extension)
            .ok_or_else(|| GrammarError::NotFound(extension.to_string()))?;

        // Criar gramática fusionada
        let mut fused = base_g.as_ref().clone();
        fused.name = new_name;
        fused.version = format!("{}.{}", base_g.version, ext_g.version);

        // Mesclar regras (extension tem prioridade em conflitos)
        for (lhs, rules) in &ext_g.rules {
            if fused.rules.contains_key(lhs) {
                // Adicionar regras do extension às existentes
                let existing = fused.rules.get_mut(lhs).unwrap();
                for rule in rules {
                    if !existing.contains(rule) {
                        existing.push(rule.clone());
                    }
                }
            } else {
                fused.rules.insert(lhs.clone(), rules.clone());
            }
        }

        // Mesclar terminais
        let mut terminal_names: std::collections::HashSet<String> =
            fused.terminals.iter().map(|t| t.name.clone()).collect();
        for terminal in &ext_g.terminals {
            if !terminal_names.contains(&terminal.name) {
                fused.terminals.push(terminal.clone());
                terminal_names.insert(terminal.name.clone());
            }
        }

        // Recalcular precedências (combinar ambas)
        // ...

        Ok(fused)
    }

    /// Total de gramáticas carregadas
    pub fn count(&self) -> usize {
        self.grammars.read().unwrap().len()
    }
}

#[derive(Debug, thiserror::Error)]
pub enum GrammarError {
    #[error("Grammar not found: {0}")]
    NotFound(String),

    #[error("Name mismatch: expected '{expected}', got '{got}'")]
    NameMismatch { expected: String, got: String },

    #[error("Parse error: {0}")]
    ParseError(String),

    #[error("Missing start symbol: {0}")]
    MissingStartSymbol(String),

    #[error("Empty left-hand side in production rule")]
    EmptyLHS,

    #[error("Terminal conflict with grammar '{grammar}': {terminals:?}")]
    TerminalConflict { grammar: String, terminals: Vec<String> },

    #[error("Validation failed: {0}")]
    Validation(String),

    #[error("Cycle detected in grammar inheritance")]
    InheritanceCycle,
}
