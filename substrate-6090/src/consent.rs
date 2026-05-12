use serde::{Serialize, Deserialize};
use chrono::Utc;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ConsentRecord {
    pub orcid: String,
    pub consent_type: ConsentType,
    pub granted_at: i64,
    pub expires_at: Option<i64>,
    pub scope: String,
    pub revoked: bool,
    pub phi_policy: PHIPolicy,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum ConsentType {
    HIPAA,
    GDPR,
    LGPD,
    Research,
    Commercialization,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PHIPolicy {
    pub allow_data_use: bool,
    pub allow_anonymization: bool,
    pub allow_sharing: bool,
    pub retention_days: u32,
}

impl ConsentRecord {
    pub fn is_valid(&self) -> bool {
        if self.revoked { return false; }
        if let Some(expiry) = self.expires_at {
            if Utc::now().timestamp() > expiry { return false; }
        }
        true
    }
}

pub struct ConsentManager {
    records: Vec<ConsentRecord>,
}

impl ConsentManager {
    pub fn new() -> Self { Self { records: vec![] } }

    pub fn register_consent(&mut self, record: ConsentRecord) {
        self.records.push(record);
    }

    pub fn revoke_consent(&mut self, orcid: &str) {
        if let Some(rec) = self.records.iter_mut().find(|r| r.orcid == orcid) {
            rec.revoked = true;
        }
    }

    pub fn get_consent(&self, orcid: &str) -> Option<&ConsentRecord> {
        self.records.iter().find(|r| r.orcid == orcid && r.is_valid())
    }
}
