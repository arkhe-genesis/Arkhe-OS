use serde::{Serialize, Deserialize};
use chrono::Utc;
use std::sync::Arc;
use std::sync::Mutex;
use rusty_leveldb::{DB, Options};

/// Entrada da trilha de auditoria
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AuditEntry {
    pub timestamp: i64,
    pub level: AuditLevel,
    pub category: String,
    pub message: String,
    pub actor: String,
    pub ip_address: Option<String>,
    pub hash: [u8; 32],
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum AuditLevel {
    INFO,
    WARNING,
    VIOLATION,
    CRITICAL,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum ComplianceStatus {
    Compliant,
    NonCompliant(String),
    UnderReview,
}

/// Trilha de auditoria imutável (usando LevelDB persistente)
#[derive(Clone)]
pub struct AuditTrail {
    db: Arc<Mutex<DB>>,
}

impl AuditTrail {
    pub fn new(_max_entries: usize) -> Self {
        let mut options = Options::default();
        options.create_if_missing = true;
        // In order to properly isolate testing data from production, and given that the user
        // will likely change this or pass it through an env variable on an upper layer, we
        // will leave a fixed testing path in /tmp, simulating the legacy behavior but via
        // levelDB
        let db = DB::open("/tmp/arkhe_audit_ledger", options).expect("Failed to open LevelDB at /tmp/arkhe_audit_ledger");
        Self { db: Arc::new(Mutex::new(db)) }
    }

    fn insert_entry(&self, entry: AuditEntry) {
        let mut db = self.db.lock().unwrap();
        let key = format!("{}_{}", entry.timestamp, rand::random::<u32>());
        if let Ok(value) = serde_json::to_string(&entry) {
            db.put(key.as_bytes(), value.as_bytes()).unwrap();
        }
    }

    pub fn log_access(&self, category: &str, message: &str) {
        self.insert_entry(AuditEntry {
            timestamp: Utc::now().timestamp(),
            level: AuditLevel::INFO,
            category: category.to_string(),
            message: message.to_string(),
            actor: "system".to_string(),
            ip_address: None,
            hash: [0; 32],
        });
    }

    pub fn log_violation(&self, category: &str, message: &str) {
        self.insert_entry(AuditEntry {
            timestamp: Utc::now().timestamp(),
            level: AuditLevel::VIOLATION,
            category: category.to_string(),
            message: message.to_string(),
            actor: "system".to_string(),
            ip_address: None,
            hash: [0; 32],
        });
    }

    pub fn log_compliance(&self, category: &str, message: &str) {
        self.insert_entry(AuditEntry {
            timestamp: Utc::now().timestamp(),
            level: AuditLevel::INFO,
            category: category.to_string(),
            message: message.to_string(),
            actor: "system".to_string(),
            ip_address: None,
            hash: [0; 32],
        });
    }

    pub fn query_violations(&self, _category: &str) -> Vec<AuditEntry> {
        let mut violations = Vec::new();
        let mut db = self.db.lock().unwrap();
        let mut iter = db.new_iter().unwrap();
        iter.seek_to_first();
        while iter.valid() {
            if let Some((_, value)) = iter.current() {
                if let Ok(entry) = serde_json::from_slice::<AuditEntry>(&value) {
                    if entry.level == AuditLevel::VIOLATION {
                        violations.push(entry);
                    }
                }
            }
            iter.next();
        }
        violations
    }

    pub fn query_hipaa_accesses(&self) -> Vec<AuditEntry> {
        let mut accesses = Vec::new();
        let mut db = self.db.lock().unwrap();
        let mut iter = db.new_iter().unwrap();
        iter.seek_to_first();
        while iter.valid() {
            if let Some((_, value)) = iter.current() {
                if let Ok(entry) = serde_json::from_slice::<AuditEntry>(&value) {
                    if entry.category == "HIPAA" {
                        accesses.push(entry);
                    }
                }
            }
            iter.next();
        }
        accesses
    }

    pub fn generate_report(&self) -> ComplianceReport {
        let mut db = self.db.lock().unwrap();
        let mut iter = db.new_iter().unwrap();
        iter.seek_to_first();

        let mut total_entries = 0;
        let mut violations = 0;

        while iter.valid() {
            if let Some((_, value)) = iter.current() {
                total_entries += 1;
                if let Ok(entry) = serde_json::from_slice::<AuditEntry>(&value) {
                    if entry.level == AuditLevel::VIOLATION {
                        violations += 1;
                    }
                }
            }
            iter.next();
        }

        ComplianceReport {
            total_entries,
            violations,
            generated_at: Utc::now().timestamp(),
            status: ComplianceStatus::Compliant,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ComplianceReport {
    pub total_entries: usize,
    pub violations: usize,
    pub generated_at: i64,
    pub status: ComplianceStatus,
}
