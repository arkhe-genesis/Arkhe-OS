//! ARKHE SQLite Canonical Store — Substrato 231
//! Compilar: cargo build --release
//! Testar: cargo test

use rusqlite::{Connection, Result, params};
use sha3::{Sha3_256, Digest};
use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct CanonicalToken {
    pub header: String,
    pub identity: String,
    pub semantics: String,
    pub payload_json: String,
    pub seal: String,
    pub timestamp: u64,
}

pub struct ArkheStore {
    conn: Connection,
}

impl ArkheStore {
    pub fn new(path: &str) -> Result<Self> {
        let conn = Connection::open(path)?;
        conn.execute_batch("
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                header TEXT NOT NULL,
                identity TEXT NOT NULL,
                semantics TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                seal TEXT NOT NULL UNIQUE,
                timestamp INTEGER NOT NULL
            );
        ")?;
        Ok(ArkheStore { conn })
    }

    pub fn insert_token(&self, token: &CanonicalToken) -> Result<usize> {
        self.conn.execute(
            "INSERT OR IGNORE INTO tokens (header, identity, semantics, payload_json, seal, timestamp)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![token.header, token.identity, token.semantics, token.payload_json, token.seal, token.timestamp],
        )
    }
}

pub fn canonical_hash(data: &[u8]) -> String {
    let mut hasher = Sha3_256::new();
    hasher.update(data);
    format!("{:x}", hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_insert_and_query() {
        let store = ArkheStore::new(":memory:").unwrap();
        let token = CanonicalToken {
            header: "hdr".into(),
            identity: "id".into(),
            semantics: "sem".into(),
            payload_json: "{}".into(),
            seal: "seal123".into(),
            timestamp: 0,
        };
        assert_eq!(store.insert_token(&token).unwrap(), 1);
    }

    #[test]
    fn test_canonical_hash() {
        let h = canonical_hash(b"test");
        assert_eq!(h.len(), 64);
    }
}

fn main() {
    println!("ARKHE SQLite Canonical Store — Substrato 231");
}
