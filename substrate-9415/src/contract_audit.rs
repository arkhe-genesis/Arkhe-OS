use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ZKProof {
    pub proof_data: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum AuditStatus {
    Aprovado,
    Reprovado,
    Pendente,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ContractAudit {
    pub address: String,
    pub last_audit_block: u64,
    pub zk_proof: ZKProof,    // prova Plonky2 de segurança
    pub audit_status: AuditStatus,
}
