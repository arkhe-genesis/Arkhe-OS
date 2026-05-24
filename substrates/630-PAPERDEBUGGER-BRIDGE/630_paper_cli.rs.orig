// src/commands/paper.rs
// ARKHE CLI Windows — Substrate 630-PAPERDEBUGGER-BRIDGE Integration
// Commands: paper-debugger, paper-critique, paper-enhance, paper-research,
//           paper-score, paper-apply-patch, paper-audit, paper-compare
// Author: ORCID 0009-0005-2697-4668
// Date: 2026-05-24

use std::path::PathBuf;
use std::process::Command;
use clap::{Args, Subcommand};

#[derive(Subcommand, Debug)]
pub enum PaperCommands {
    /// Initialize PaperDebugger session with Overleaf URL
    Debugger {
        #[arg(value_name = "OVERLEAF_URL")]
        url: String,
    },
    /// Run Reviewer agent (AAAI-style critique)
    Critique {
        #[arg(value_name = "FILE")]
        file: PathBuf,
        #[arg(value_name = "SELECTION", optional = true)]
        selection: Option<String>,
        #[arg(long)]
        json: bool,
    },
    /// Run Enhancer agent (rewriting/refinement)
    Enhance {
        #[arg(value_name = "FILE")]
        file: PathBuf,
        #[arg(value_name = "SELECTION", optional = true)]
        selection: Option<String>,
        #[arg(long)]
        json: bool,
    },
    /// Run Researcher agent (literature search)
    Research {
        #[arg(value_name = "QUERY")]
        query: Vec<String>,
        #[arg(long)]
        json: bool,
    },
    /// Run Scoring agent (clarity/coherence)
    Score {
        #[arg(value_name = "FILE")]
        file: PathBuf,
        #[arg(long)]
        json: bool,
    },
    /// Apply diff patch to LaTeX file
    ApplyPatch {
        #[arg(value_name = "PATCH_FILE")]
        patch: PathBuf,
        #[arg(value_name = "TARGET_FILE")]
        target: PathBuf,
    },
    /// Anchor session to temporal blockchain
    Audit {
        #[arg(value_name = "SESSION_FILE")]
        session: PathBuf,
        #[arg(long, default_value = "k51qzi5uqu5dlxgpwjkkiyqik8btk7pa07y76ca7zy8mqse6i5bzjukmivefwe")]
        ipns_key: String,
    },
    /// Compare two papers side-by-side
    Compare {
        #[arg(value_name = "PAPER_A")]
        paper_a: PathBuf,
        #[arg(value_name = "PAPER_B")]
        paper_b: PathBuf,
        #[arg(long)]
        json: bool,
    },
}

fn get_bridge_path() -> Result<PathBuf, String> {
    let mut exe_path = std::env::current_exe().map_err(|e| format!("Failed to get current executable path: {}", e))?;
    exe_path.pop();
    exe_path.push("paper_debugger_bridge.py");
    Ok(exe_path)
}

pub fn handle_paper(cmd: PaperCommands) -> Result<(), String> {
    let bridge_path = get_bridge_path()?;
    match cmd {
        PaperCommands::Debugger { url } => {
            println!("📝 [630] Initializing PaperDebugger session");
            println!("   URL: {}", url);

            let mut python_cmd = Command::new("python3");
            let current_dir = std::env::current_dir().map_err(|e| format!("Failed to get current directory: {}", e))?;
            python_cmd
                .arg(&bridge_path)
                .arg("connect")
                .arg(&url)
                .current_dir(current_dir);

            let output = python_cmd.output().map_err(|e| e.to_string())?;
            println!("{}", String::from_utf8_lossy(&output.stdout));
            if !output.status.success() {
                return Err("[630] Failed to initialize session".to_string());
            }
            Ok(())
        }

        PaperCommands::Critique { file, selection, json } => {
            if !file.exists() {
                return Err(format!("File not found: {}", file.display()));
            }
            println!("🔍 [630→Reviewer] Running AAAI-style critique...");

            let mut python_cmd = Command::new("python3");
            python_cmd.arg(&bridge_path).arg("critique").arg(&file);
            if let Some(sel) = selection {
                python_cmd.arg(&sel);
            }

            let output = python_cmd.output().map_err(|e| e.to_string())?;
            let stdout = String::from_utf8_lossy(&output.stdout);

            if json {
                // Wrap in JSON
                let result = json!({
                    "agent": "reviewer",
                    "file": file.to_string_lossy(),
                    "output": stdout.trim(),
                    "status": if output.status.success() { "success" } else { "error" }
                });
                let json_str = serde_json::to_string_pretty(&result).map_err(|e| e.to_string())?;
                println!("{}", json_str);
            } else {
                println!("{}", stdout);
            }

            if output.status.success() {
                println!("✅ [630→Reviewer] Critique complete");
                Ok(())
            } else {
                Err("[630→Reviewer] Critique failed".to_string())
            }
        }

        PaperCommands::Enhance { file, selection, json } => {
            if !file.exists() {
                return Err(format!("File not found: {}", file.display()));
            }
            println!("✨ [630→Enhancer] Running XtraGPT enhancement...");

            let mut python_cmd = Command::new("python3");
            python_cmd.arg(&bridge_path).arg("enhance").arg(&file);
            if let Some(sel) = selection {
                python_cmd.arg(&sel);
            }

            let output = python_cmd.output().map_err(|e| e.to_string())?;
            let stdout = String::from_utf8_lossy(&output.stdout);

            if json {
                let result = json!({
                    "agent": "enhancer",
                    "file": file.to_string_lossy(),
                    "output": stdout.trim(),
                    "status": if output.status.success() { "success" } else { "error" }
                });
                let json_str = serde_json::to_string_pretty(&result).map_err(|e| e.to_string())?;
                println!("{}", json_str);
            } else {
                println!("{}", stdout);
            }

            if output.status.success() {
                println!("✅ [630→Enhancer] Enhancement complete");
                Ok(())
            } else {
                Err("[630→Enhancer] Enhancement failed".to_string())
            }
        }

        PaperCommands::Research { query, json } => {
            let query_str = query.join(" ");
            println!("📚 [630→Researcher] Searching literature: '{}'...", query_str);

            let mut python_cmd = Command::new("python3");
            python_cmd.arg(&bridge_path).arg("research").arg(&query_str);

            let output = python_cmd.output().map_err(|e| e.to_string())?;
            let stdout = String::from_utf8_lossy(&output.stdout);

            if json {
                let result = json!({
                    "agent": "researcher",
                    "query": query_str,
                    "output": stdout.trim(),
                    "status": if output.status.success() { "success" } else { "error" }
                });
                let json_str = serde_json::to_string_pretty(&result).map_err(|e| e.to_string())?;
                println!("{}", json_str);
            } else {
                println!("{}", stdout);
            }

            if output.status.success() {
                println!("✅ [630→Researcher] Literature search complete");
                Ok(())
            } else {
                Err("[630→Researcher] Search failed".to_string())
            }
        }

        PaperCommands::Score { file, json } => {
            if !file.exists() {
                return Err(format!("File not found: {}", file.display()));
            }
            println!("📊 [630→Scorer] Evaluating document quality...");

            let mut python_cmd = Command::new("python3");
            python_cmd.arg(&bridge_path).arg("score").arg(&file);

            let output = python_cmd.output().map_err(|e| e.to_string())?;
            let stdout = String::from_utf8_lossy(&output.stdout);

            if json {
                let result = json!({
                    "agent": "scorer",
                    "file": file.to_string_lossy(),
                    "output": stdout.trim(),
                    "status": if output.status.success() { "success" } else { "error" }
                });
                let json_str = serde_json::to_string_pretty(&result).map_err(|e| e.to_string())?;
                println!("{}", json_str);
            } else {
                println!("{}", stdout);
            }

            if output.status.success() {
                println!("✅ [630→Scorer] Evaluation complete");
                Ok(())
            } else {
                Err("[630→Scorer] Evaluation failed".to_string())
            }
        }

        PaperCommands::ApplyPatch { patch, target } => {
            if !patch.exists() {
                return Err(format!("Patch file not found: {}", patch.display()));
            }
            if !target.exists() {
                return Err(format!("Target file not found: {}", target.display()));
            }
            println!("🔧 [630] Applying patch {} to {}...", patch.display(), target.display());

            // Use git apply or patch command
            let mut cmd = Command::new("git");
            let parent_dir = target.parent().ok_or("Target file has no parent directory")?;
            cmd.arg("apply").arg(&patch).current_dir(parent_dir);

            let output = cmd.output().map_err(|e| e.to_string())?;
            if output.status.success() {
                println!("✅ [630] Patch applied successfully");
                Ok(())
            } else {
                let stderr = String::from_utf8_lossy(&output.stderr);
                Err(format!("[630] Patch failed: {}", stderr))
            }
        }

        PaperCommands::Audit { session, ipns_key } => {
            if !session.exists() {
                return Err(format!("Session file not found: {}", session.display()));
            }
            println!("🔗 [630→561] Anchoring session to temporal chain...");
            println!("🔑 [630→547] IPNS key: {}", ipns_key);

            let mut python_cmd = Command::new("python3");
            python_cmd.arg(&bridge_path).arg("audit").arg(&session);

            let output = python_cmd.output().map_err(|e| e.to_string())?;
            let stdout = String::from_utf8_lossy(&output.stdout);
            println!("{}", stdout);

            if output.status.success() {
                println!("✅ [630] Session anchored to temporal chain");
                Ok(())
            } else {
                Err("[630] Anchor failed".to_string())
            }
        }

        PaperCommands::Compare { paper_a, paper_b, json } => {
            if !paper_a.exists() {
                return Err(format!("Paper A not found: {}", paper_a.display()));
            }
            if !paper_b.exists() {
                return Err(format!("Paper B not found: {}", paper_b.display()));
            }
            println!("⚖️  [630] Comparing papers...");

            let mut python_cmd = Command::new("python3");
            python_cmd
                .arg(&bridge_path)
                .arg("compare")
                .arg(&paper_a)
                .arg(&paper_b);

            let output = python_cmd.output().map_err(|e| e.to_string())?;
            let stdout = String::from_utf8_lossy(&output.stdout);

            if json {
                let result = json!({
                    "agent": "comparator",
                    "paper_a": paper_a.to_string_lossy(),
                    "paper_b": paper_b.to_string_lossy(),
                    "output": stdout.trim(),
                    "status": if output.status.success() { "success" } else { "error" }
                });
                let json_str = serde_json::to_string_pretty(&result).map_err(|e| e.to_string())?;
                println!("{}", json_str);
            } else {
                println!("{}", stdout);
            }

            if output.status.success() {
                println!("✅ [630] Comparison complete");
                Ok(())
            } else {
                Err("[630] Comparison failed".to_string())
            }
        }
    }
}
