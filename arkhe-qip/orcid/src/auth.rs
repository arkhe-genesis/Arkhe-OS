
use std::collections::HashMap;
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OrcidRecord {
    pub orcid_id: String,
    pub access_token: String,
    pub refresh_token: Option<String>,
    pub token_expires_at: u64,
    pub authenticated_at: u64,
    pub public_key_fingerprint: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OrcidToken {}

#[derive(Debug)]
pub enum OrcidAuthError {
    OAuthError(String),
}

pub struct OrcidAuth {}


impl std::fmt::Display for OrcidAuthError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}
impl std::error::Error for OrcidAuthError {}
