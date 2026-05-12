use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct OnboardRequest {
    pub orcid: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OnboardResponse {
    pub success: bool,
    pub vendor_id: String,
    pub message: String,
}

pub async fn onboard_vendor(req: OnboardRequest) -> Result<OnboardResponse, anyhow::Error> {
    // Simulating onboarding logic
    Ok(OnboardResponse {
        success: true,
        vendor_id: format!("vendor_{}", req.orcid),
        message: format!("Vendor with ORCID {} successfully onboarded.", req.orcid),
    })
}
