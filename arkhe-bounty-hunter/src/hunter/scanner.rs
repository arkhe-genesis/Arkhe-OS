// ============================================================================
// ARKHE Bounty Hunter — Scanner Principal
// ============================================================================
// Motor de varredura multi-linguagem que coordena análise estática,
// ML detection, e fuzzing dinâmico para encontrar vulnerabilidades.
// ============================================================================

use std::sync::{Arc, Mutex, mpsc};
use std::path::{Path, PathBuf};
use std::time::Instant;
use rayon::prelude::*;
use crossbeam::channel;

use crate::{
    VulnScanner, VulnAnalyzer, VulnFuzzer, VulnId, Vulnerability,
    FileAnalysis, AnalysisStats, HunterConfig, VulnLocation,
    Exploitability, Severity, OutputFormat,
};
use crate::patterns::vulnerability_db::VulnerabilityDB;
use crate::ml::vulnerability_classifier::VulnClassifier;
use crate::temporal::blame_chain::BlameChain;

/// Resultado de uma operação de scan
#[derive(Clone, Debug)]
pub struct ScanResult {
    pub total_files: usize,
    pub total_vulnerabilities: usize,
    pub by_severity: [usize; 6], // Critical, High, Medium, Low, Info, FalsePositive
    pub by_cwe: std::collections::HashMap<String, usize>,
    pub files_analyzed: Vec<FileAnalysis>,
    pub total_time_ms: u64,
    pub avg_confidence: f64,
    pub exploits_verified: usize,
}

pub struct MLVulnPrediction {
    pub line: u32,
    pub confidence: f64,
    pub file: String,
    pub pattern: String,
    pub cwe_id: String,
    pub owasp_category: Option<String>,
    pub severity: Severity,
    pub cvss_score: f32,
    pub title: String,
    pub description: String,
    pub column: u32,
    pub end_line: u32,
    pub end_column: u32,
    pub function: Option<String>,
    pub language: String,
    pub remediation: String,
}

/// Scanner principal — orquestra toda a análise
pub struct VulnScannerImpl {
    config: HunterConfig,
    analyzer: VulnAnalyzer,
    classifier: Option<VulnClassifier>,
    fuzzer: Option<VulnFuzzer>,
    blame_chain: Option<BlameChain>,
    vuln_db: Arc<VulnerabilityDB>,
    scan_count: usize,
}

impl VulnScannerImpl {
    /// Criar novo scanner com configuração
    pub fn new(config: HunterConfig) -> Self {
        let analyzer = VulnAnalyzer::new(config.clone());
        let classifier = if config.enable_ml {
            Some(VulnClassifier::new())
        } else {
            None
        };

        let fuzzer = if config.enable_fuzzing {
            Some(VulnFuzzer::new(
                config.concurrent_scans,
                config.timeout_per_file_secs,
            ))
        } else {
            None
        };

        Self {
            config,
            analyzer,
            classifier,
            fuzzer,
            blame_chain: None,
            vuln_db: Arc::new(VulnerabilityDB::load_default()),
            scan_count: 0,
        }
    }

    /// Configurar rastreamento temporal (Blame Chain)
    pub fn with_temporal_tracking(mut self, repo_path: &Path) -> Self {
        self.blame_chain = BlameChain::new(repo_path).ok();
        self
    }

    /// Scan de um arquivo individual
    pub fn scan_file(
        &self,
        file_path: &Path,
        source: &str,
        language: &str,
    ) -> Result<FileAnalysis, ScanError> {
        let start = Instant::now();

        // === Fase 1: Análise Estática com Padrões ===
        let mut vulnerabilities = self.analyzer.analyze(source, language, file_path)?;

        // === Fase 2: Classificação ML ===
        if let Some(classifier) = &self.classifier {
            let ml_vulns = classifier.classify(source, language, &vulnerabilities);
            self.merge_ml_results(&mut vulnerabilities, ml_vulns);
        }

        // === Fase 3: Verificação de Falsos Positivos ===
        let initial_count = vulnerabilities.len();
        vulnerabilities.retain(|v| {
            !self.is_false_positive(v, source)
        });
        let false_positives_filtered = initial_count - vulnerabilities.len();

        // === Fase 4: Verificação de Exploitabilidade ===
        if let Some(fuzzer) = &self.fuzzer {
            self.verify_exploits(&mut vulnerabilities, fuzzer, language);
        }

        // === Fase 5: Rastreamento Temporal ===
        if let Some(blame) = &self.blame_chain {
            for vuln in &mut vulnerabilities {
                vuln.temporal_info = blame.get_blame_info(
                    file_path,
                    vuln.location.line,
                    &vuln.pattern_matched,
                );
            }
        }

        let elapsed = start.elapsed().as_millis() as u64;

        let stats = AnalysisStats {
            lines_scanned: source.lines().count() as u64,
            patterns_checked: self.vuln_db.pattern_count() as u64,
            patterns_matched: vulnerabilities.len() as u64 + false_positives_filtered as u64,
            ml_inferences: self.classifier.as_ref().map(|_| vulnerabilities.len() as u64).unwrap_or(0),
            false_positives_filtered: false_positives_filtered as u64,
            exploits_verified: vulnerabilities.iter().filter(|v| v.proof_available).count() as u64,
            unique_cwes: {
                let mut cwes: Vec<_> = vulnerabilities.iter().map(|v| v.cwe_id.clone()).collect();
                cwes.sort();
                cwes.dedup();
                cwes.len()
            },
            max_severity: vulnerabilities.iter()
                .map(|v| v.severity)
                .max()
                .unwrap_or(Severity::Info),
        };

        Ok(FileAnalysis {
            file: file_path.display().to_string(),
            language: language.to_string(),
            vulnerabilities,
            stats,
            scan_time_ms: elapsed,
        })
    }

    /// Scan recursivo de diretório
    pub fn scan_directory(
        &self,
        dir: &Path,
        extensions: &[&str],
    ) -> Result<ScanResult, ScanError> {
        let files = self.collect_source_files(dir, extensions)?;

        let total_files = files.len();
        let results: Vec<FileAnalysis> = files
            .par_iter()
            .filter_map(|(path, lang, source)| {
                self.scan_file(path, source, lang)
                    .map_err(|e| {
                        eprintln!("Error scanning {}: {}", path.display(), e);
                        e
                    })
                    .ok()
            })
            .collect();

        // Agregar resultados
        let total_time_ms = results.iter().map(|r| r.scan_time_ms).sum();
        let total_vulns: usize = results.iter().map(|r| r.vulnerabilities.len()).sum();

        let (by_severity, by_cwe) = self.aggregate_stats(&results);

        let avg_confidence = if total_vulns > 0 {
            results.iter()
                .flat_map(|r| r.vulnerabilities.iter())
                .map(|v| v.confidence)
                .sum::<f64>() / total_vulns as f64
        } else {
            0.0
        };

        let exploits_verified = results.iter()
            .map(|r| r.stats.exploits_verified as usize)
            .sum();

        Ok(ScanResult {
            total_files,
            total_vulnerabilities: total_vulns,
            by_severity,
            by_cwe,
            files_analyzed: results,
            total_time_ms,
            avg_confidence,
            exploits_verified,
        })
    }

    /// Scan incremental — apenas arquivos modificados
    pub fn scan_incremental(
        &mut self,
        dir: &Path,
        since_commit: Option<&str>,
    ) -> Result<ScanResult, ScanError> {
        if let Some(blame) = &self.blame_chain {
            let changed_files = blame.get_changed_files(since_commit)?;
            let extensions = self.get_supported_extensions();

            let files: Vec<_> = changed_files.into_iter()
                .filter(|f| {
                    extensions.iter().any(|ext| f.ends_with(ext))
                })
                .collect();

            let total_files = files.len();
            let results: Vec<FileAnalysis> = files
                .par_iter()
                .filter_map(|file_path| {
                    let source = std::fs::read_to_string(file_path).ok()?;
                    let lang = self.detect_language(Path::new(file_path));
                    self.scan_file(Path::new(file_path), &source, &lang).ok()
                })
                .collect();

            let total_vulns: usize = results.iter().map(|r| r.vulnerabilities.len()).sum();
            let total_time_ms = results.iter().map(|r| r.scan_time_ms).sum();

            let (by_severity, by_cwe) = self.aggregate_stats(&results);

            Ok(ScanResult {
                total_files,
                total_vulnerabilities: total_vulns,
                by_severity,
                by_cwe,
                files_analyzed: results,
                total_time_ms,
                avg_confidence: 0.0,
                exploits_verified: 0,
            })
        } else {
            Err(ScanError::TemporalNotEnabled)
        }
    }

    /// Coletar arquivos fonte do diretório
    fn collect_source_files(
        &self,
        dir: &Path,
        extensions: &[&str],
    ) -> Result<Vec<(PathBuf, String, String)>, ScanError> {
        let mut files = Vec::new();

        if !dir.is_dir() {
            return Err(ScanError::NotADirectory(dir.display().to_string()));
        }

        // Mock directory traversal

        Ok(files)
    }

    /// Detectar linguagem por extensão
    fn detect_language(&self, path: &Path) -> String {
        let ext = path.extension()
            .and_then(|e| e.to_str())
            .unwrap_or("")
            .to_lowercase();

        match ext.as_str() {
            "rs" => "rust",
            "py" => "python",
            "js" | "mjs" | "cjs" => "javascript",
            "ts" | "mts" | "cts" => "typescript",
            "c" => "c",
            "cpp" | "cc" | "cxx" => "cpp",
            "go" => "go",
            "zig" => "zig",
            "java" => "java",
            "rb" => "ruby",
            "lua" => "lua",
            "sql" => "sql",
            "sol" => "solidity",
            "cairo" => "cairo",
            "nr" => "noir",
            "move" => "move",
            "wat" => "wat",
            "pro" | "pl" => "prolog",
            "cypher" => "cypher",
            "rq" | "sparql" => "sparql",
            _ => "unknown",
        }.to_string()
    }

    /// Mesclar resultados de ML com análise estática
    fn merge_ml_results(
        &self,
        vulnerabilities: &mut Vec<Vulnerability>,
        ml_results: Vec<MLVulnPrediction>,
    ) {
        for ml_pred in ml_results {
            if let Some(existing) = vulnerabilities.iter_mut()
                .find(|v| v.location.line == ml_pred.line)
            {
                // Atualizar confiança com dado do ML
                existing.ml_score = Some(ml_pred.confidence);
                existing.confidence = (existing.confidence + ml_pred.confidence) / 2.0;
            } else {
                // Nova vulnerabilidade detectada apenas pelo ML
                vulnerabilities.push(Vulnerability {
                    id: VulnId::new(&ml_pred.file, ml_pred.line, &ml_pred.pattern),
                    cwe_id: ml_pred.cwe_id,
                    owasp_category: ml_pred.owasp_category,
                    severity: ml_pred.severity,
                    cvss_score: ml_pred.cvss_score,
                    title: ml_pred.title,
                    description: ml_pred.description,
                    location: VulnLocation {
                        file: ml_pred.file,
                        line: ml_pred.line,
                        column: ml_pred.column,
                        end_line: ml_pred.end_line,
                        end_column: ml_pred.end_column,
                        function: ml_pred.function,
                        module: None,
                    },
                    language: ml_pred.language,
                    pattern_matched: ml_pred.pattern,
                    exploitability: Exploitability::NotExploitable,
                    remediation: ml_pred.remediation,
                    code_snippet: None,
                    fix_suggestion: None,
                    confidence: ml_pred.confidence,
                    ml_score: Some(ml_pred.confidence),
                    temporal_info: None,
                    is_false_positive: false,
                    proof_available: false,
                });
            }
        }
    }

    /// Verificar exploitabilidade dos bugs encontrados
    fn verify_exploits(
        &self,
        vulnerabilities: &mut Vec<Vulnerability>,
        fuzzer: &VulnFuzzer,
        language: &str,
    ) {
        for vuln in vulnerabilities.iter_mut() {
            if vuln.severity < Severity::High {
                continue; // Não verificar vulnerabilidades baixas
            }

            match fuzzer.verify_exploit(vuln, language) {
                Ok(exploit_result) => {
                    vuln.proof_available = exploit_result.proof_available;
                    vuln.exploitability = if exploit_result.confirmed {
                        Exploitability::ConfirmedExploit
                    } else if exploit_result.partial {
                        Exploitability::High
                    } else {
                        Exploitability::NotExploitable
                    };

                    if let Some(fix) = exploit_result.fix_suggestion {
                        vuln.fix_suggestion = Some(fix);
                    }
                }
                Err(_) => {
                    // Falha na verificação — marcar como não verificado
                    vuln.exploitability = Exploitability::Medium;
                }
            }
        }
    }

    /// Verificar se é falso positivo
    fn is_false_positive(&self, vuln: &Vulnerability, source: &str) -> bool {
        // Verificação heurística de falsos positivos:
        // 1. Comentários ignorando o warning
        // 2. Supressões explícitas
        // 3. Padrões conhecidos de legado
        // 4. Contexto semântico

        let line = vuln.location.line as usize;
        let lines: Vec<&str> = source.lines().collect();

        if line > 0 && line <= lines.len() {
            let current = lines[line - 1];
            let above = if line >= 2 { lines.get(line - 2) } else { None };

            // Verificar supressões
            if current.contains("arkhe:ignore")
                || current.contains("# arkhe-disable")
                || current.contains("// bountysafe")
            {
                return true;
            }

            if above.map_or(false, |l| {
                l.contains("arkhe:ignore-next")
                || l.contains("# arkhe-disable-next-line")
            }) {
                return true;
            }
        }

        false
    }

    /// Agregar estatísticas
    fn aggregate_stats(
        &self,
        results: &[FileAnalysis],
    ) -> ([usize; 6], std::collections::HashMap<String, usize>) {
        let mut by_severity = [0; 6];
        let mut by_cwe: std::collections::HashMap<String, usize> = std::collections::HashMap::new();

        for result in results {
            for vuln in &result.vulnerabilities {
                match vuln.severity {
                    Severity::Critical => by_severity[0] += 1,
                    Severity::High => by_severity[1] += 1,
                    Severity::Medium => by_severity[2] += 1,
                    Severity::Low => by_severity[3] += 1,
                    Severity::Info => by_severity[4] += 1,
                    Severity::FalsePositive => by_severity[5] += 1,
                }

                *by_cwe.entry(vuln.cwe_id.clone()).or_insert(0) += 1;
            }
        }

        (by_severity, by_cwe)
    }

    /// Gerar relatório do scan
    pub fn generate_report(&self, result: &ScanResult) -> String {
        let format = self.config.output_format;

        match format {
            OutputFormat::Json => self.report_json(result),
            OutputFormat::Markdown => self.report_markdown(result),
            OutputFormat::Sarif => self.report_sarif(result),
            OutputFormat::Html => self.report_html(result),
            OutputFormat::Mermaid => self.report_mermaid(result),
        }
    }

    fn report_json(&self, result: &ScanResult) -> String {
        serde_json::to_string_pretty(result).unwrap_or_default()
    }

    fn report_markdown(&self, result: &ScanResult) -> String {
        let mut md = String::new();

        md.push_str("# 🐛 ARKHE Bug Bounty Report\n\n");
        md.push_str(&format!("## Summary\n\n"));
        md.push_str(&format!("| Metric | Value |\n"));
        md.push_str(&format!("|--------|-------|\n"));
        md.push_str(&format!("| Files Scanned | {} |\n", result.total_files));
        md.push_str(&format!("| Total Vulnerabilities | {} |\n", result.total_vulnerabilities));
        md.push_str(&format!("| Scan Time | {}ms |\n", result.total_time_ms));
        md.push_str(&format!("| Avg Confidence | {:.1}% |\n", result.avg_confidence * 100.0));
        md.push_str(&format!("| Exploits Verified | {} |\n", result.exploits_verified));

        md.push_str("\n## Severity Breakdown\n\n");
        md.push_str("| Severity | Count |\n");
        md.push_str("|----------|-------|\n");
        let labels = ["Critical", "High", "Medium", "Low", "Info", "False Positive"];
        for (i, count) in result.by_severity.iter().enumerate() {
            if *count > 0 {
                md.push_str(&format!("| {} | {} |\n", labels[i], count));
            }
        }

        md.push_str("\n## Top CWEs\n\n");
        md.push_str("| CWE | Count |\n");
        md.push_str("|-----|-------|\n");
        let mut cwes: Vec<_> = result.by_cwe.iter().collect();
        cwes.sort_by(|a, b| b.1.cmp(a.1));
        for (cwe, count) in cwes.iter().take(10) {
            md.push_str(&format!("| {} | {} |\n", cwe, count));
        }

        md.push_str("\n## Vulnerabilities\n\n");
        for file_analysis in &result.files_analyzed {
            if file_analysis.vulnerabilities.is_empty() { continue; }

            md.push_str(&format!("### {}\n\n", file_analysis.file));

            for vuln in &file_analysis.vulnerabilities {
                let emoji = match vuln.severity {
                    Severity::Critical => "🔴",
                    Severity::High => "🟠",
                    Severity::Medium => "🟡",
                    Severity::Low => "🟢",
                    _ => "⚪",
                };

                md.push_str(&format!(
                    "{} **[{}]** {} ({})\n",
                    emoji, vuln.id.to_hex(), vuln.title, vuln.cwe_id
                ));
                md.push_str(&format!("Location: `{}:{}`\n", vuln.location.file, vuln.location.line));
                md.push_str(&format!("Confidence: {:.1}%\n", vuln.confidence * 100.0));
                md.push_str(&format!("Severity: {:?}\n", vuln.severity));
                md.push_str(&format!("Pattern: `{}`\n", vuln.pattern_matched));
                md.push_str(&format!("\n{}\n\n", vuln.description));

                if let Some(ref fix) = vuln.fix_suggestion {
                    md.push_str(&format!("### 🔧 Fix\n```{}\n```\n", fix));
                }

                if let Some(ref snippet) = vuln.code_snippet {
                    md.push_str(&format!("### Code Snippet\n```{}\n```\n", snippet));
                }
            }
        }

        md
    }

    fn report_sarif(&self, result: &ScanResult) -> String {
        // SARIF format for GitHub Code Scanning integration
        let sarif = serde_json::json!({
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "arkhe-bounty-hunter",
                        "version": "5.6.0",
                        "informationUri": "https://github.com/arkhe-os/bounty-hunter",
                        "rules": []
                    }
                },
                "results": result.files_analyzed.iter().flat_map(|fa| {
                    fa.vulnerabilities.iter().map(|v| {
                        serde_json::json!({
                            "ruleId": v.cwe_id,
                            "ruleIndex": 0,
                            "level": match v.severity {
                                Severity::Critical => "error",
                                Severity::High => "error",
                                Severity::Medium => "warning",
                                _ => "note",
                            },
                            "message": { "text": v.title },
                            "locations": [{
                                "physicalLocation": {
                                    "artifactLocation": { "uri": v.location.file },
                                    "region": {
                                        "startLine": v.location.line,
                                        "startColumn": v.location.column,
                                        "endLine": v.location.end_line,
                                        "endColumn": v.location.end_column,
                                    }
                                }
                            }]
                        })
                    })
                }).collect::<Vec<_>>()
            }]
        });

        sarif.to_string()
    }

    fn report_html(&self, result: &ScanResult) -> String {
        let mermaid = self.report_mermaid(result);

        format!(r#"<!DOCTYPE html>
<html>
<head>
    <title>ARKHE Bug Bounty Report</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{ startOnLoad: true }});</script>
    <style>
        body {{ font-family: 'Inter', sans-serif; max-width: 1200px; margin: 0 auto; padding: 2rem; background: #0d1117; color: #c9d1d9; }}
        h1 {{ color: #f85149; }}
        .stat {{ background: #161b22; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; }}
        .critical {{ border-left: 4px solid #f85149; }}
        .high {{ border-left: 4px solid #d29922; }}
        .medium {{ border-left: 4px solid #58a6ff; }}
        .low {{ border-left: 4px solid #3fb950; }}
    </style>
</head>
<body>
    <h1>🐛 ARKHE Bug Bounty Report</h1>
    {}
    <h2>Vulnerability Flow</h2>
    {}
</body>
</html>"#, self.report_markdown(result), mermaid)
    }

    fn report_mermaid(&self, result: &ScanResult) -> String {
        let mut lines = vec![
            "graph TD".to_string(),
            "    A[Source Code] --> B[UAST Analysis]".to_string(),
            "    B --> C[Pattern Matching]".to_string(),
            "    B --> D[ML Classification]".to_string(),
            "    C --> E[Vulnerability Found]".to_string(),
            "    D --> E".to_string(),
            "    E --> F{Severity?}".to_string(),
            "    F -->|Critical| G[Exploit Verification]".to_string(),
            "    F -->|High| G".to_string(),
            "    F -->|Medium| H[Report]".to_string(),
            "    F -->|Low| H".to_string(),
            "    G -->|Confirmed| I[Exploit Proof]".to_string(),
            "    G -->|Not Exploitable| H".to_string(),
            "    I --> J[Temporal Chain Registration]".to_string(),
            "    J --> K[Bounty Registration]".to_string(),
            "    H --> L[Remediation]".to_string(),
        ];

        // Add vulnerability nodes
        let mut id = 0;
        for fa in &result.files_analyzed {
            for vuln in &fa.vulnerabilities {
                id += 1;
                let color = match vuln.severity {
                    Severity::Critical => "#f85149",
                    Severity::High => "#d29922",
                    Severity::Medium => "#58a6ff",
                    _ => "#3fb950",
                };
                lines.push(format!(
                    "    E --> V{}[\"{}<br/>{}:{}\"]",
                    id, vuln.cwe_id, vuln.location.file, vuln.location.line
                ));
                lines.push(format!("    style V{} fill:{}", id, color));
            }
        }

        lines.insert(0, "```mermaid".to_string());
        lines.push("```".to_string());
        lines.join("\n")
    }

    fn get_supported_extensions(&self) -> Vec<&'static str> {
        vec!["rs", "py", "js", "ts", "c", "cpp", "go", "java"]
    }
}

/// Scan error types
#[derive(Debug, thiserror::Error)]
pub enum ScanError {
    #[error("Not a directory: {0}")]
    NotADirectory(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Parse error: {0}")]
    ParseError(String),

    #[error("Pattern error: {0}")]
    PatternError(String),

    #[error("Temporal tracking not enabled")]
    TemporalNotEnabled,

    #[error("ML model not loaded")]
    ModelNotLoaded,
}
pub type VulnScanner = VulnScannerImpl;
