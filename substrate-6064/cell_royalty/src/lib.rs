pub mod data_valuation;
pub mod hipaa_bridge;

pub mod x402_pix_bridge {
    pub struct PixIpcClient;
    impl PixIpcClient {
        pub async fn send_pix_royalty(&self, _key: &str, _cents: u64, _memo: &str) -> Result<(), crate::RoyaltyError> {
            Ok(())
        }
    }
}

pub struct CellState {
    pub data: Vec<f64>,
}

#[derive(Debug)]
pub enum RoyaltyError {
    NoConsent,
    Other(String),
}

impl std::fmt::Display for RoyaltyError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}

pub struct ConsentStatus {
    pub allow_data_use: bool,
    pub phi_policy: PHIPolicy,
}

#[derive(Clone, Copy)]
pub enum PHIPolicy {
    Strict,
}
