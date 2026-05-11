// ============================================================================
// ARKHE Bounty Hunter — Vulnerability Pattern Registry
// ============================================================================
// Central registry for all known vulnerability patterns.
// Each pattern maps to a CWE, has detection logic, and severity guidance.
// ============================================================================

pub mod vulnerability_db;
pub mod cwe_registry;
pub mod owasp_top10;
pub mod temporal_patterns;
pub mod injection;
pub mod crypto;
pub mod memory;
pub mod logic;

use std::collections::HashMap;
use serde::{Deserialize, Serialize};

/// A vulnerability detection pattern
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PatternRule {
    pub id: String,
    pub cwe_id: String,
    pub name: String,
    pub description: String,
    pub pattern: PatternDefinition,
    pub language_specific: bool,
    pub languages: Vec<String>,
    pub severity_default: SeverityLevel,
    pub confidence: f64,
    pub remediation: String,
    pub fix: Option<String>,
    pub owasp_category: Option<String>,
    pub examples_vulnerable: Vec<String>,
    pub examples_safe: Vec<String>,
}

/// How a pattern is defined
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum PatternDefinition {
    /// Regex-based pattern matching on source code
    Regex {
        pattern: String,
        flags: Option<String>,
    },
    /// AST-based pattern using UAST node structure
    AstPattern {
        node_type: String,
        attributes: HashMap<String, String>,
        children_pattern: Option<Box<PatternDefinition>>,
    },
    /// Data flow pattern (source → sink without sanitizer)
    DataFlow {
        sources: Vec<String>,
        sinks: Vec<String>,
        sanitizers: Vec<String>,
    },
    /// Taint propagation pattern
    TaintPropagation {
        entry_point: String,
        dangerous_call: String,
        requires_sanitization: bool,
    },
    /// Sequence of operations (temporal pattern)
    Sequence {
        steps: Vec<PatternStep>,
        max_gap: Option<u32>,
    },
    /// Combination of patterns (AND/OR/NOT)
    Composite {
        operator: CompositeOp,
        patterns: Vec<PatternDefinition>,
    },
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum CompositeOp {
    And,
    Or,
    Not,
}

/// A step in a temporal sequence pattern
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PatternStep {
    pub name: String,
    pub pattern: PatternDefinition,
    pub optional: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum SeverityLevel {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

/// Database of all known vulnerability patterns
pub struct VulnerabilityDatabase {
    patterns: HashMap<String, PatternRule>,
    by_cwe: HashMap<String, Vec<String>>,
    by_language: HashMap<String, Vec<String>>,
    by_category: HashMap<String, Vec<String>>,
}

impl VulnerabilityDatabase {
    pub fn new() -> Self {
        Self {
            patterns: HashMap::new(),
            by_cwe: HashMap::new(),
            by_language: HashMap::new(),
            by_category: HashMap::new(),
        }
    }

    pub fn register(&mut self, pattern: PatternRule) {
        let id = pattern.id.clone();
        let cwe = pattern.cwe_id.clone();
        let categories = pattern.owasp_category.clone();

        // Add to main index
        for lang in &pattern.languages {
            self.by_language.entry(lang.clone())
                .or_insert_with(Vec::new)
                .push(id.clone());
        }

        self.by_cwe.entry(cwe)
            .or_insert_with(Vec::new)
            .push(id.clone());

        if let Some(cat) = categories {
            self.by_category.entry(cat)
                .or_insert_with(Vec::new)
                .push(id.clone());
        }

        self.patterns.insert(id, pattern);
    }

    pub fn get_pattern(&self, id: &str) -> Option<&PatternRule> {
        self.patterns.get(id)
    }

    pub fn get_by_cwe(&self, cwe: &str) -> Vec<&PatternRule> {
        self.by_cwe.get(cwe)
            .map(|ids| ids.iter().filter_map(|id| self.patterns.get(id)).collect())
            .unwrap_or_default()
    }

    pub fn get_patterns_for_language(&self, language: &str) -> Vec<&PatternRule> {
        self.by_language.get(language)
            .map(|ids| ids.iter().filter_map(|id| self.patterns.get(id)).collect())
            .unwrap_or_default()
    }

    pub fn get_dangerous_apis(&self, _language: &str) -> HashMap<String, ApiDangerInfo> {
        // Return dangerous API mappings for a language
        HashMap::new() // Placeholder
    }

    pub fn pattern_count(&self) -> usize {
        self.patterns.len()
    }
}

pub struct ApiDangerInfo {
    pub cwe_id: String,
    pub description: String,
    pub owasp_category: Option<String>,
    pub default_severity: SeverityLevel,
    pub default_cvss: f32,
    pub default_exploitability: crate::Exploitability,
    pub remediation: String,
    pub safe_alternative: String,
}

pub type PatternRuleRef<'a> = &'a PatternRule;
pub type VulnerabilityDB = VulnerabilityDatabase;

impl VulnerabilityDatabase {
    pub fn load_default() -> Self {
        Self::new()
    }
}
