//! ARKHE OS Substrato 231: SQLite Canonical Store
//! Canon: ∞.Ω.∇+++.231.sqlite_rust
//!
//! Armazena Tokens Arkhe, Proposições Verificadas, Evidências e Selos Temporais
//! com integridade garantida via Rust e SQLite.

use rusqlite::{Connection, Result, params};
use serde::{Deserialize, Serialize};
use sha3::{Sha3_256, Digest};
use std::time::{SystemTime, UNIX_EPOCH};

// =============================================================================
// ESTRUTURAS CANÔNICAS
// =============================================================================

#[derive(Debug, Serialize, Deserialize)]
pub struct CanonicalToken {
    pub header: String,
    pub identity: String,
    pub semantics: String,
    pub payload_json: String,
    pub seal: String,
    pub timestamp: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct VerifiedProposition {
    pub id: Option<i64>,
    pub source_hash: String,
    pub phi_c: f64,
    pub violations: String,  // JSON array de strings
    pub is_valid: bool,
    pub verified_at: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EvidenceRecord {
    pub hash: String,
    pub data_blob: Vec<u8>,
    pub timestamp: u64,
}

// =============================================================================
// GERENCIADOR DE BANCO DE DADOS
// =============================================================================

pub struct ArkheStore {
    conn: Connection,
}

impl ArkheStore {
    /// Abre (ou cria) o banco de dados no caminho especificado
    pub fn new(path: &str) -> Result<Self> {
        let conn = Connection::open(path)?;
        // Configurar WAL para melhor concorrência
        conn.pragma_update(None, "journal_mode", "WAL")?;
        conn.pragma_update(None, "synchronous", "NORMAL")?;
        conn.pragma_update(None, "foreign_keys", "ON")?;

        let store = ArkheStore { conn };
        store.create_tables()?;
        Ok(store)
    }

    fn create_tables(&self) -> Result<()> {
        self.conn.execute_batch("
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                header TEXT NOT NULL,
                identity TEXT NOT NULL,
                semantics TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                seal TEXT NOT NULL UNIQUE,
                timestamp INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS verified_propositions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_hash TEXT NOT NULL,
                phi_c REAL NOT NULL,
                violations TEXT NOT NULL,
                is_valid INTEGER NOT NULL,
                verified_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evidence (
                hash TEXT PRIMARY KEY,
                data_blob BLOB NOT NULL,
                timestamp INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tokens_seal ON tokens(seal);
            CREATE INDEX IF NOT EXISTS idx_tokens_identity ON tokens(identity);
            CREATE INDEX IF NOT EXISTS idx_prop_phi ON verified_propositions(phi_c);
        ")?;
        Ok(())
    }

    // ─── TOKENS ────────────────────────────────────────

    pub fn insert_token(&self, token: &CanonicalToken) -> Result<usize> {
        self.conn.execute(
            "INSERT OR IGNORE INTO tokens (header, identity, semantics, payload_json, seal, timestamp)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                token.header,
                token.identity,
                token.semantics,
                token.payload_json,
                token.seal,
                token.timestamp
            ],
        )
    }

    pub fn get_token_by_seal(&self, seal: &str) -> Result<Option<CanonicalToken>> {
        self.conn.query_row(
            "SELECT header, identity, semantics, payload_json, seal, timestamp FROM tokens WHERE seal = ?1",
            params![seal],
            |row| {
                Ok(CanonicalToken {
                    header: row.get(0)?,
                    identity: row.get(1)?,
                    semantics: row.get(2)?,
                    payload_json: row.get(3)?,
                    seal: row.get(4)?,
                    timestamp: row.get(5)?,
                })
            },
        ).optional()
    }

    pub fn list_tokens_by_identity(&self, identity: &str, limit: usize) -> Result<Vec<CanonicalToken>> {
        let mut stmt = self.conn.prepare(
            "SELECT header, identity, semantics, payload_json, seal, timestamp
             FROM tokens WHERE identity = ?1 ORDER BY timestamp DESC LIMIT ?2"
        )?;
        let tokens = stmt.query_map(params![identity, limit as i64], |row| {
            Ok(CanonicalToken {
                header: row.get(0)?,
                identity: row.get(1)?,
                semantics: row.get(2)?,
                payload_json: row.get(3)?,
                seal: row.get(4)?,
                timestamp: row.get(5)?,
            })
        })?;
        tokens.collect()
    }

    // ─── PROPOSIÇÕES VERIFICADAS ──────────────────────

    pub fn insert_verified_proposition(&self, prop: &VerifiedProposition) -> Result<usize> {
        self.conn.execute(
            "INSERT INTO verified_propositions (source_hash, phi_c, violations, is_valid, verified_at)
             VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                prop.source_hash,
                prop.phi_c,
                prop.violations,
                prop.is_valid as i32,
                prop.verified_at
            ],
        )
    }

    pub fn get_propositions_above_phi(&self, threshold: f64, limit: usize) -> Result<Vec<VerifiedProposition>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, source_hash, phi_c, violations, is_valid, verified_at
             FROM verified_propositions WHERE phi_c >= ?1 ORDER BY phi_c DESC LIMIT ?2"
        )?;
        let props = stmt.query_map(params![threshold, limit as i64], |row| {
            Ok(VerifiedProposition {
                id: Some(row.get(0)?),
                source_hash: row.get(1)?,
                phi_c: row.get(2)?,
                violations: row.get(3)?,
                is_valid: row.get::<_, i32>(4)? != 0,
                verified_at: row.get(5)?,
            })
        })?;
        props.collect()
    }

    // ─── EVIDÊNCIAS ──────────────────────────────────

    pub fn store_evidence(&self, evidence: &EvidenceRecord) -> Result<usize> {
        self.conn.execute(
            "INSERT OR IGNORE INTO evidence (hash, data_blob, timestamp) VALUES (?1, ?2, ?3)",
            params![evidence.hash, evidence.data_blob, evidence.timestamp],
        )
    }

    pub fn get_evidence(&self, hash: &str) -> Result<Option<EvidenceRecord>> {
        self.conn.query_row(
            "SELECT hash, data_blob, timestamp FROM evidence WHERE hash = ?1",
            params![hash],
            |row| {
                Ok(EvidenceRecord {
                    hash: row.get(0)?,
                    data_blob: row.get(1)?,
                    timestamp: row.get(2)?,
                })
            },
        ).optional()
    }

    // ─── MÉTRICAS ────────────────────────────────────

    pub fn stats(&self) -> Result<ArkheStoreStats> {
        let token_count: i64 = self.conn.query_row("SELECT COUNT(*) FROM tokens", [], |r| r.get(0))?;
        let prop_count: i64 = self.conn.query_row("SELECT COUNT(*) FROM verified_propositions", [], |r| r.get(0))?;
        let evidence_count: i64 = self.conn.query_row("SELECT COUNT(*) FROM evidence", [], |r| r.get(0))?;
        let avg_phi: f64 = self.conn.query_row("SELECT COALESCE(AVG(phi_c), 0.0) FROM verified_propositions", [], |r| r.get(0))?;
        Ok(ArkheStoreStats { token_count, prop_count, evidence_count, avg_phi })
    }
}

#[derive(Debug, Serialize)]
pub struct ArkheStoreStats {
    pub token_count: i64,
    pub prop_count: i64,
    pub evidence_count: i64,
    pub avg_phi: f64,
}

// =============================================================================
// UTILITÁRIOS CANÔNICOS
// =============================================================================

/// Calcula SHA3-256 de um slice de bytes e retorna hex string
pub fn canonical_hash(data: &[u8]) -> String {
    let mut hasher = Sha3_256::new();
    hasher.update(data);
    format!("{:x}", hasher.finalize())
}

/// Timestamp atual em segundos desde UNIX_EPOCH
pub fn now_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}

// Trait para converter rusqlite::Result<Option<T>> para Option<T>
pub trait OptionalExt<T> {
    fn optional(self) -> Result<Option<T>>;
}

impl<T> OptionalExt<T> for Result<T> {
    fn optional(self) -> Result<Option<T>> {
        match self {
            Ok(val) => Ok(Some(val)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e),
        }
    }
}
