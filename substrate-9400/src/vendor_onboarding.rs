use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VendorInfo {
    pub orcid: String,
    pub name: String,
}

pub fn validate_vendor(info: &VendorInfo) -> bool {
    !info.orcid.is_empty()
}
