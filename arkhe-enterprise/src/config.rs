#[derive(Clone, Default)]
pub struct EnterpriseConfig {
    pub tenants: TenantConfig,
    pub rbac: RBACConfig,
    pub audit: AuditConfig,
    pub billing: BillingConfig,
    pub sla: SLAConfig,
    pub orchestration: OrchestrationConfig,
    pub compliance: ComplianceConfig,
    pub financial: FinancialConfig,
    pub api: ApiConfig,
}

#[derive(Clone, Default)]
pub struct TenantConfig {}

#[derive(Clone, Default)]
pub struct BillingConfig {}

#[derive(Clone, Default)]
pub struct SLAConfig {}

#[derive(Clone, Default)]
pub struct RBACConfig {}

#[derive(Clone, Default)]
pub struct AuditConfig {}

#[derive(Clone, Default)]
pub struct MonitoringConfig {}

#[derive(Clone, Default)]
pub struct ComplianceConfig {}

#[derive(Clone, Default)]
pub struct OrchestrationConfig {}

#[derive(Clone, Default)]
pub struct FinancialConfig {}

#[derive(Clone, Default)]
pub struct ApiConfig {
    pub enable_grpc: bool,
    pub enable_rest: bool,
    pub grpc_port: u16,
    pub rest_port: u16,
}
