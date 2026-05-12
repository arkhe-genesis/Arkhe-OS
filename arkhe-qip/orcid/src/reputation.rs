
use std::collections::HashMap;
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, Hash)]
pub enum ReputationSource {
    Publications,
    Citations,
    Datasets,
    Software,
    PeerReview,
    Grants,
    Awards,
    Education,
    Employment,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct ReputationScore {
    pub total_score: f64,
    pub breakdown: HashMap<ReputationSource, f64>,
    pub publication_count: u32,
    pub total_citations: u32,
    pub h_index: u32,
    pub dataset_count: u32,
    pub academic_age: u32,
    pub last_updated: u64,
}
