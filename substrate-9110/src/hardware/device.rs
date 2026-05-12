/// Interface comum para qualquer hardware NVIDIA espacial.
#[async_trait::async_trait]
pub trait SpaceHardware: Send + Sync {
    async fn provision(&mut self) -> Result<(), HardwareError>;
    async fn deploy_shard(&self, shard: &ShardConfig) -> Result<(), HardwareError>;
    async fn health_check(&self) -> Result<HealthStatus, HardwareError>;
    async fn power_profile(&self) -> PowerMetrics;
    async fn secure_attestation(&self) -> Result<AttestationProof, HardwareError>;
}

pub struct ShardConfig {
    pub shard_id: String,
}

#[derive(Debug)]
pub enum HardwareError {
    ConnectionFailed,
    ProvisioningFailed,
    DeploymentFailed,
    AttestationFailed,
}

pub struct HealthStatus {
    pub is_healthy: bool,
}

pub struct PowerMetrics {
    pub draw_watts: f64,
}

pub struct AttestationProof {
    pub hash: String,
    pub proof: String,
    pub timestamp: u64,
}
