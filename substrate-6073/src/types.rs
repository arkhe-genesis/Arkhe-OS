use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationManifest {
    pub package_type: String,
    pub generated_at: String,
    pub current_value_date: String,
    pub watermark: String,
    pub status: String,
    pub reference: String, // UUID
    pub uetr: String,      // Unique End‑to‑end Transaction Reference
    pub amount: String,    // as string for precision
    pub currency: String,
    pub files: Vec<FileEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileEntry {
    pub file: String,
    pub sha256: String,
    pub size_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignedManifest {
    pub algorithm: String, // "HMAC-SHA256"
    pub key_label: String,
    pub signature: String,       // hex
    pub manifest_sha256: String, // hex
    pub manifest: ValidationManifest,
}
