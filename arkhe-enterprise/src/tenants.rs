use crate::config::TenantConfig;
pub struct TenantManager {}
impl TenantManager {
    pub fn new(_configs: &[TenantConfig]) -> Self { Self {} }
    pub async fn provision_tenants(&self) -> Result<(), Box<dyn std::error::Error>> { Ok(()) }
    pub async fn reconcile_quotas(&self) {}
}
pub struct Tenant {}
pub struct TenantId {}
pub struct TenantQuota {}
pub struct TenantStatus {}
