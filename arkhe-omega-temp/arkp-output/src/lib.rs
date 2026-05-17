
use colored::*;
use serde::Serialize;
use std::fmt;

pub trait OutputFormatter: Send + Sync {
    fn display(&self, result: &FormattedResult);
}

#[derive(Serialize)]
pub struct FormattedResult {
    pub success: bool,
    pub message: String,
    pub data: Option<serde_json::Value>,
    pub canonical_hash: String,
}

pub struct RichFormatter {
    pub use_color: bool,
}

impl OutputFormatter for RichFormatter {
    fn display(&self, r: &FormattedResult) {
        let icon = if r.success { "✔".green() } else { "✘".red() };
        let msg = if r.success { r.message.clone() } else { r.message.red().to_string() };
        println!("{} {}", icon, msg);
        if let Some(data) = &r.data {
            println!("  {}", serde_json::to_string_pretty(data).unwrap_or_default().dimmed());
        }
        println!("  seal: {}", r.canonical_hash.dimmed());
    }
}

pub struct JsonFormatter;
impl OutputFormatter for JsonFormatter {
    fn display(&self, r: &FormattedResult) {
        println!("{}", serde_json::to_string(r).unwrap());
    }
}
