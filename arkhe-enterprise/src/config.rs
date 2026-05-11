#[derive(Clone)]
pub struct EnterpriseConfig {
    pub tenants: Vec<TenantConfig>,
    pub rbac: RBACConfig,
    pub audit: AuditConfig,
    pub billing: BillingConfig,
    pub sla: SLAConfig,
    pub orchestration: OrchestrationConfig,
    pub compliance: ComplianceConfig,
    pub financial: FinancialConfig,
    pub api: ApiConfig,
}

#[derive(Clone)]
pub struct TenantConfig {}
#[derive(Clone)]
pub struct RBACConfig {}
#[derive(Clone)]
pub struct AuditConfig {}
#[derive(Clone)]
pub struct BillingConfig {}
#[derive(Clone)]
pub struct SLAConfig {}
#[derive(Clone)]
pub struct OrchestrationConfig {}
#[derive(Clone)]
pub struct ComplianceConfig {}
#[derive(Clone)]
pub struct FinancialConfig {}
#[derive(Clone)]
pub struct ApiConfig {
    pub enable_grpc: bool,
    pub enable_rest: bool,
    pub grpc_port: u16,
    pub rest_port: u16,
}
#[derive(Clone)]
pub struct MonitoringConfig {}
