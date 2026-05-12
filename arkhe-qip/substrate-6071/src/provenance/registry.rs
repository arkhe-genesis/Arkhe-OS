use std::collections::{HashMap, HashSet};
use serde::{Serialize, Deserialize};

use super::super::types::DataFingerprint;

pub struct ProvenanceRegistry {
    fingerprint_to_orcids: HashMap<Vec<u8>, HashSet<String>>,
    orcid_to_fingerprints: HashMap<String, HashSet<Vec<u8>>>,
    contribution_types: HashMap<Vec<u8>, String>,
    registration_timestamps: HashMap<Vec<u8>, u64>,
}

impl ProvenanceRegistry {
    pub fn new() -> Self {
        Self {
            fingerprint_to_orcids: HashMap::new(),
            orcid_to_fingerprints: HashMap::new(),
            contribution_types: HashMap::new(),
            registration_timestamps: HashMap::new(),
        }
    }

    pub fn get_contributors(&self, fingerprint: &[u8]) -> Vec<&String> {
        self.fingerprint_to_orcids
            .get(fingerprint)
            .map(|s| s.iter().collect())
            .unwrap_or_default()
    }
}
