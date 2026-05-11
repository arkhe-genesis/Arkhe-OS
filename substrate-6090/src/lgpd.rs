use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum LGPDRight {
    Access,
    Rectification,
    Erasure,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LGPDRequest {
    pub right: LGPDRight,
    pub data_subject: String,
}

pub struct LGPDCompliance;
