use crate::config::FinancialConfig;
pub struct FinancialHub {}
impl FinancialHub {
    pub fn new(_config: &FinancialConfig) -> Self { Self {} }
    pub async fn initialize(&self) -> Result<(), Box<dyn std::error::Error>> { Ok(()) }
}
pub struct SwiftGateway {}
pub struct PixGateway {}
pub struct MT103Message {}
pub struct PACS008Message {}
pub struct CAMT053Message {}
