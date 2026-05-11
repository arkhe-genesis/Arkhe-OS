// ============================================================================
// ARKHE Bounty Hunter — Static Analysis Engine
// ============================================================================
// Deep static analysis using UAST patterns, data flow analysis,
// and taint propagation to find vulnerabilities.
// ============================================================================

use std::collections::{HashMap, HashSet, VecDeque};
use std::sync::Arc;

use crate::{
    VulnLocation, Vulnerability, VulnId,
    Exploitability, Severity,
};
use crate::patterns::vulnerability_db::VulnerabilityDB;
use crate::hunter::severity::Classification;

/// Static analysis configuration
#[derive(Clone, Debug)]
pub struct AnalyzerConfig {
    pub enable_data_flow: bool,
    pub enable_taint_analysis: bool,
    pub enable_control_flow: bool,
    pub enable_api_audit: bool,
    pub enable_pattern_matching: bool,
    pub max_depth: u32,
    pub follow_includes: bool,
}

impl Default for AnalyzerConfig {
    fn default() -> Self {
        Self {
            enable_data_flow: true,
            enable_taint_analysis: true,
            enable_control_flow: true,
            enable_api_audit: true,
            enable_pattern_matching: true,
            max_depth: 100,
            follow_includes: true,
        }
    }
}

/// VulnAnalyzer — performs deep static analysis on UAST
pub struct VulnAnalyzer {
    config: AnalyzerConfig,
    vuln_db: Arc<VulnerabilityDB>,
}

impl VulnAnalyzer {
    pub fn new(config: crate::HunterConfig) -> Self {
        Self {
            config: AnalyzerConfig {
                enable_data_flow: true,
                enable_taint_analysis: true,
                enable_control_flow: true,
                enable_api_audit: true,
                enable_pattern_matching: true,
                max_depth: config.max_depth,
                follow_includes: true,
            },
            vuln_db: Arc::new(VulnerabilityDB::load_default()),
        }
    }

    /// Main analysis entry point
    pub fn analyze(
        &self,
        source: &str,
        language: &str,
        file_path: &std::path::Path,
    ) -> Result<Vec<Vulnerability>, AnalysisError> {
        let mut vulnerabilities = Vec::new();

        // Build UAST from source
        let uast = self.build_uast(source, language)?;

        // === Analysis Pass 1: Pattern Matching ===
        if self.config.enable_pattern_matching {
            let pattern_vulns = self.pattern_analysis(&uast, source, language);
            vulnerabilities.extend(pattern_vulns);
        }

        // === Analysis Pass 2: Data Flow Analysis ===
        if self.config.enable_data_flow {
            let flow_vulns = self.data_flow_analysis(&uast, source, language);
            vulnerabilities.extend(flow_vulns);
        }

        // === Analysis Pass 3: Taint Analysis ===
        if self.config.enable_taint_analysis {
            let taint_vulns = self.taint_analysis(&uast, source, language);
            vulnerabilities.extend(taint_vulns);
        }

        // === Analysis Pass 4: Control Flow ===
        if self.config.enable_control_flow {
            let flow_vulns = self.control_flow_analysis(&uast, source, language);
            vulnerabilities.extend(flow_vulns);
        }

        // === Analysis Pass 5: API Audit ===
        if self.config.enable_api_audit {
            let api_vulns = self.api_audit(&uast, source, language);
            vulnerabilities.extend(api_vulns);
        }

        // Deduplicate
        self.deduplicate(&mut vulnerabilities);

        // Classify severity
        for vuln in &mut vulnerabilities {
            self.classify_severity(vuln);
        }

        Ok(vulnerabilities)
    }

    // ============================
    // ANALYSIS PASS 1: PATTERN MATCHING
    // ============================

    fn pattern_analysis(
        &self,
        uast: &impl UastView,
        source: &str,
        language: &str,
    ) -> Vec<Vulnerability> {
        let mut vulns = Vec::new();
        let patterns = self.vuln_db.get_patterns_for_language(language);

        for pattern in patterns {
            let matches = self.match_pattern(uast, pattern);
            for m in matches {
                vulns.push(Vulnerability {
                    id: VulnId::new(
                        &format!("file:{}", m.node_id),
                        m.line,
                        &pattern.cwe_id,
                    ),
                    cwe_id: pattern.cwe_id.clone(),
                    owasp_category: pattern.owasp_category.clone(),
                    severity: Severity::Medium, // Will be classified later
                    cvss_score: 0.0,
                    title: pattern.name.clone(),
                    description: pattern.description.clone(),
                    location: VulnLocation {
                        file: "source".to_string(),
                        line: m.line,
                        column: m.column,
                        end_line: m.end_line,
                        end_column: m.end_column,
                        function: m.function.clone(),
                        module: m.module.clone(),
                    },
                    language: language.to_string(),
                    pattern_matched: pattern.id.clone(),
                    exploitability: Exploitability::NotExploitable,
                    remediation: pattern.remediation.clone(),
                    code_snippet: m.snippet.clone(),
                    fix_suggestion: pattern.fix.clone(),
                    confidence: pattern.confidence,
                    ml_score: None,
                    temporal_info: None,
                    is_false_positive: false,
                    proof_available: false,
                });
            }
        }

        vulns
    }

    // ============================
    // ANALYSIS PASS 2: DATA FLOW ANALYSIS
    // ============================

    fn data_flow_analysis(
        &self,
        uast: &impl UastView,
        source: &str,
        language: &str,
    ) -> Vec<Vulnerability> {
        let mut vulns = Vec::new();

        // Track data flow from sources to sinks
        let sources = self.find_taint_sources(uast);
        let sinks = self.find_taint_sinks(uast);

        for source in &sources {
            for sink in &sinks {
                if self.is_data_flow_reachable(uast, source, sink) {
                    // Check for sanitization between source and sink
                    let sanitizer = self.find_sanitizer(uast, source, sink);
                    if sanitizer.is_none() {
                        vulns.push(Vulnerability {
                            id: VulnId::new("dataflow", source.line, "CWE-20"),
                            cwe_id: "CWE-20".to_string(),
                            owasp_category: Some("A03:2021-Injection".to_string()),
                            severity: Severity::High,
                            cvss_score: 8.1,
                            title: format!("Unsanitized Data Flow: {} → {}", source.name, sink.name),
                            description: format!(
                                "Data from '{}' flows to '{}' without sanitization. \
                                This may allow injection or unexpected behavior.",
                                source.name, sink.name
                            ),
                            location: VulnLocation {
                                file: "source".to_string(),
                                line: sink.line,
                                column: sink.column,
                                end_line: sink.end_line,
                                end_column: sink.end_column,
                                function: sink.function.clone(),
                                module: None,
                            },
                            language: language.to_string(),
                            pattern_matched: "DATA_FLOW_UNSANITIZED".to_string(),
                            exploitability: Exploitability::High,
                            remediation: "Add input validation or sanitization between source and sink."
                                .to_string(),
                            code_snippet: None,
                            fix_suggestion: Some(format!("sanitize({})", source.name)),
                            confidence: 0.85,
                            ml_score: None,
                            temporal_info: None,
                            is_false_positive: false,
                            proof_available: false,
                        });
                    }
                }
            }
        }

        vulns
    }

    // ============================
    // ANALYSIS PASS 3: TAINT ANALYSIS
    // ============================

    fn taint_analysis(
        &self,
        uast: &impl UastView,
        source: &str,
        language: &str,
    ) -> Vec<Vulnerability> {
        let mut vulns = Vec::new();

        // Propagate taint marks through the program
        let mut taint_map: HashMap<u64, TaintMark> = HashMap::new();

        // Mark sources
        for node in uast.nodes_iter() {
            if self.is_taint_source(node.as_ref()) {
                taint_map.insert(node.id(), TaintMark {
                    source: "user_input".to_string(),
                    kind: TaintKind::Untrusted,
                    propagated_from: None,
                });
            }
        }

        // Propagate through assignments, function calls, etc.
        let mut changed = true;
        let mut iterations = 0;
        while changed && iterations < 100 {
            changed = false;
            iterations += 1;

            for node in uast.nodes_iter() {
                self.propagate_taint(node.as_ref(), &mut taint_map, &mut changed);
            }
        }

        // Check for taint at dangerous sinks
        for node in uast.nodes_iter() {
            if self.is_dangerous_sink(node.as_ref()) {
                if let Some(taint) = taint_map.get(&node.id()) {
                    vulns.push(Vulnerability {
                        id: VulnId::new("taint", node.line(), "CWE-990"),
                        cwe_id: "CWE-990".to_string(),
                        owasp_category: Some("A03:2021-Injection".to_string()),
                        severity: Severity::High,
                        cvss_score: 7.5,
                        title: format!("Tainted Data at {}: origin={}",
                            self.sink_name(node.as_ref()), taint.source),
                        description: format!(
                            "Tainted data from '{}' reaches {} without sanitization. \
                            Taint kind: {:?}",
                            taint.source, self.sink_name(node.as_ref()), taint.kind
                        ),
                        location: VulnLocation {
                            file: "source".to_string(),
                            line: node.line(),
                            column: node.column(),
                            end_line: node.end_line(),
                            end_column: node.end_column(),
                            function: node.function().map(|s| s.to_string()),
                            module: None,
                        },
                        language: language.to_string(),
                        pattern_matched: format!("TAINT_{:?}", taint.kind),
                        exploitability: Exploitability::High,
                        remediation: "Sanitize input before use in sensitive operation."
                            .to_string(),
                        code_snippet: None,
                        fix_suggestion: Some("sanitize(input)".to_string()),
                        confidence: 0.9,
                        ml_score: None,
                        temporal_info: None,
                        is_false_positive: false,
                        proof_available: false,
                    });
                }
            }
        }

        vulns
    }

    // ============================
    // ANALYSIS PASS 4: CONTROL FLOW
    // ============================

    fn control_flow_analysis(
        &self,
        uast: &impl UastView,
        source: &str,
        language: &str,
    ) -> Vec<Vulnerability> {
        let mut vulns = Vec::new();

        // Detect: TOCTOU (Time of Check, Time of Use)
        let toctou = self.detect_toctou(uast);
        vulns.extend(toctou);

        // Detect: Missing authorization checks
        let auth_vulns = self.detect_missing_auth(uast);
        vulns.extend(auth_vulns);

        // Detect: Double fetch
        let double_fetch = self.detect_double_fetch(uast);
        vulns.extend(double_fetch);

        vulns
    }

    // ============================
    // ANALYSIS PASS 5: API AUDIT
    // ============================

    fn api_audit(
        &self,
        uast: &impl UastView,
        source: &str,
        language: &str,
    ) -> Vec<Vulnerability> {
        let mut vulns = Vec::new();

        // Check for dangerous API usage
        let dangerous_apis = self.vuln_db.get_dangerous_apis(language);

        for node in uast.nodes_iter() {
            if let Some(api_name) = self.get_api_call_name(node.as_ref()) {
                if let Some(api_info) = dangerous_apis.get(&api_name) {
                    vulns.push(Vulnerability {
                        id: VulnId::new("api", node.line(), &api_info.cwe_id),
                        cwe_id: api_info.cwe_id.clone(),
                        owasp_category: api_info.owasp_category.clone(),
                        severity: api_info.default_severity.clone().into(),
                        cvss_score: api_info.default_cvss,
                        title: format!("Dangerous API: {}", api_name),
                        description: api_info.description.clone(),
                        location: VulnLocation {
                            file: "source".to_string(),
                            line: node.line(),
                            column: node.column(),
                            end_line: node.end_line(),
                            end_column: node.end_column(),
                            function: node.function().map(|s| s.to_string()),
                            module: None,
                        },
                        language: language.to_string(),
                        pattern_matched: format!("DANGEROUS_API:{}", api_name),
                        exploitability: api_info.default_exploitability.clone(),
                        remediation: api_info.remediation.clone(),
                        code_snippet: None,
                        fix_suggestion: Some(api_info.safe_alternative.clone()),
                        confidence: 0.95,
                        ml_score: None,
                        temporal_info: None,
                        is_false_positive: false,
                        proof_available: false,
                    });
                }
            }
        }

        vulns
    }

    // ============================
    // UTILITY METHODS
    // ============================

    fn deduplicate(&self, vulns: &mut Vec<Vulnerability>) {
        let mut seen: HashSet<(String, u32, String)> = HashSet::new();
        vulns.retain(|v| {
            let key = (v.location.file.clone(), v.location.line, v.cwe_id.clone());
            seen.insert(key)
        });
    }

    fn classify_severity(&self, vuln: &mut Vulnerability) {
        // CVSS-based classification
        vuln.cvss_score = self.calculate_cvss(vuln);

        vuln.severity = if vuln.cvss_score >= 9.0 {
            Severity::Critical
        } else if vuln.cvss_score >= 7.0 {
            Severity::High
        } else if vuln.cvss_score >= 4.0 {
            Severity::Medium
        } else if vuln.cvss_score > 0.0 {
            Severity::Low
        } else {
            Severity::Info
        };
    }

    fn calculate_cvss(&self, vuln: &Vulnerability) -> f32 {
        // Simplified CVSS v3.1 calculation
        let base = match vuln.cwe_id.as_str() {
            // SQL Injection, Command Injection, XSS — High base
            "CWE-89" | "CWE-78" | "CWE-79" | "CWE-94" => 9.8,
            // Buffer overflow, use-after-free
            "CWE-120" | "CWE-416" | "CWE-787" => 9.8,
            // Path traversal
            "CWE-22" => 7.5,
            // Hardcoded credentials
            "CWE-798" => 7.8,
            // Insecure deserialization
            "CWE-502" => 8.6,
            // Race conditions
            "CWE-362" | "CWE-367" => 7.5,
            // Weak crypto
            "CWE-327" | "CWE-328" => 5.9,
            // Missing auth
            "CWE-306" => 7.3,
            // Default/unknown
            _ => 5.3,
        };

        // Adjust based on exploitability
        let exploit_factor = match vuln.exploitability {
            Exploitability::ConfirmedExploit => 1.2,
            Exploitability::High => 1.1,
            Exploitability::Medium => 1.0,
            Exploitability::Low => 0.9,
            Exploitability::NotExploitable => 0.7,
        };

        (base * exploit_factor).min(10.0)
    }

    fn build_uast(&self, source: &str, language: &str) -> Result<impl UastView, AnalysisError> {
        // Build UAST from source code using ARKHE P³
        // This would use the PolyglotParser from the polyglot module
        // For now, returns a placeholder
        Ok(UastPlaceholder)
    }

    fn find_taint_sources(&self, uast: &impl UastView) -> Vec<TaintSource> {
        vec![] // Placeholder
    }

    fn find_taint_sinks(&self, uast: &impl UastView) -> Vec<TaintSink> {
        vec![] // Placeholder
    }

    fn is_data_flow_reachable(&self, uast: &impl UastView, source: &TaintSource, sink: &TaintSink) -> bool {
        false // Placeholder
    }

    fn find_sanitizer(&self, uast: &impl UastView, source: &TaintSource, sink: &TaintSink) -> Option<()> {
        None // Placeholder
    }

    fn is_taint_source(&self, node: &impl UastNodeView) -> bool {
        // Check if node represents untrusted input
        matches!(node.kind_name(),
            "FunctionParam" | "ExternalCall" | "ReadInput" | "HTTPRequest")
    }

    fn is_dangerous_sink(&self, node: &impl UastNodeView) -> bool {
        // Check if node represents a dangerous operation
        matches!(node.kind_name(),
            "EvalCall" | "ExecCall" | "SQLQuery" | "ShellExec" |
            "FileWrite" | "SystemCall" | "Deserialization")
    }

    fn sink_name(&self, node: &impl UastNodeView) -> String {
        node.kind_name().to_string()
    }

    fn detect_toctou(&self, uast: &impl UastView) -> Vec<Vulnerability> {
        vec![] // Placeholder for TOCTOU detection
    }

    fn detect_missing_auth(&self, uast: &impl UastView) -> Vec<Vulnerability> {
        vec![] // Placeholder for missing auth detection
    }

    fn detect_double_fetch(&self, uast: &impl UastView) -> Vec<Vulnerability> {
        vec![] // Placeholder for double-fetch detection
    }

    fn get_api_call_name(&self, node: &impl UastNodeView) -> Option<String> {
        node.attributes().get("name").cloned()
    }

    fn propagate_taint(&self, node: &impl UastNodeView, taint_map: &mut HashMap<u64, TaintMark>, changed: &mut bool) {
        // Propagate taint through assignments and function calls
        // Implementation would traverse UAST children
        let _ = (node, taint_map, changed);
    }

    fn match_pattern(&self, uast: &impl UastView, pattern: &crate::patterns::PatternRule) -> Vec<PatternMatch> {
        let mut matches = Vec::new();
        // Walk UAST and find pattern matches
        let _ = (uast, pattern);
        matches
    }
}

// ====================
// Supporting Types
// ====================

struct TaintMark {
    source: String,
    kind: TaintKind,
    propagated_from: Option<u64>,
}

#[derive(Clone, Copy, Debug, PartialEq)]
enum TaintKind {
    Untrusted,
    UserControlled,
    CrossOrigin,
    Environment,
    Database,
}

struct TaintSource {
    name: String,
    line: u32,
    column: u32,
    taint_kind: TaintKind,
}

struct TaintSink {
    name: String,
    line: u32,
    column: u32,
    function: Option<String>,
    end_line: u32,
    end_column: u32,
}

struct PatternMatch {
    line: u32,
    column: u32,
    end_line: u32,
    end_column: u32,
    function: Option<String>,
    module: Option<String>,
    snippet: Option<String>,
    node_id: u64,
}

// Trait abstractions for UAST viewing
trait UastView {
    fn nodes_iter(&self) -> Box<dyn Iterator<Item = Box<dyn UastNodeView>>>;
}

trait UastNodeView {
    fn id(&self) -> u64;
    fn kind_name(&self) -> &str;
    fn line(&self) -> u32;
    fn column(&self) -> u32;
    fn end_line(&self) -> u32;
    fn end_column(&self) -> u32;
    fn function(&self) -> Option<&str>;
    fn attributes(&self) -> &HashMap<String, String>;
}

struct UastPlaceholder;
impl UastView for UastPlaceholder {
    fn nodes_iter(&self) -> Box<dyn Iterator<Item = Box<dyn UastNodeView>>> {
        Box::new(std::iter::empty())
    }
}

#[derive(Debug, thiserror::Error)]
pub enum AnalysisError {
    #[error("Parse error: {0}")]
    ParseError(String),

    #[error("UAST build failed: {0}")]
    UastError(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Pattern error: {0}")]
    PatternError(String),
}

impl From<crate::patterns::SeverityLevel> for Severity {
    fn from(s: crate::patterns::SeverityLevel) -> Self {
        match s {
            crate::patterns::SeverityLevel::Critical => Severity::Critical,
            crate::patterns::SeverityLevel::High => Severity::High,
            crate::patterns::SeverityLevel::Medium => Severity::Medium,
            crate::patterns::SeverityLevel::Low => Severity::Low,
            crate::patterns::SeverityLevel::Info => Severity::Info,
        }
    }
}
