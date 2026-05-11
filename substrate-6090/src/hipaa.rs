use crate::audit::{AuditTrail, ComplianceStatus, AuditEntry};
use crate::consent::{ConsentManager, ConsentRecord};
use crate::anonymization::{AnonymizationEngine, DeIdentifiedData};
use serde::{Serialize, Deserialize};

/// Configuração de conformidade HIPAA
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct HIPAAConfig {
    /// Método de de‑identificação (Safe Harbor ou Expert Determination)
    pub deid_method: DeIdentificationMethod,
    /// Manter trilha de auditoria de acessos
    pub audit_access: bool,
    /// Criptografar dados em repouso
    pub encrypt_at_rest: bool,
    /// Criptografar dados em trânsito
    pub encrypt_in_transit: bool,
    /// Política de retenção de PHI (dias)
    pub retention_days: u32,
    /// Notificar paciente sobre acesso não autorizado
    pub breach_notification: bool,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq)]
pub enum DeIdentificationMethod {
    SafeHarbor,        // remover 18 identificadores
    ExpertDetermination, // análise estatística de risco
}

/// Engine de conformidade HIPAA
pub struct HIPAACompliance {
    config: HIPAAConfig,
    anonymizer: AnonymizationEngine,
    _consent_mgr: ConsentManager,
    audit: AuditTrail,
}

impl HIPAACompliance {
    pub fn new(config: HIPAAConfig, audit: AuditTrail) -> Self {
        Self {
            config,
            anonymizer: AnonymizationEngine::new(),
            _consent_mgr: ConsentManager::new(),
            audit,
        }
    }

    /// Verifica se um dado de paciente pode ser processado
    pub fn verify_patient_data(&self, data: &[u8], consent: &ConsentRecord) -> Result<DeIdentifiedData, HIPAAViolation> {
        // 1. Verificar consentimento
        if !consent.is_valid() {
            self.audit.log_violation("HIPAA", "Missing or expired consent");
            return Err(HIPAAViolation::NoConsent);
        }

        // 2. De‑identificar dados conforme método configurado
        let deid = self.anonymizer.deidentify(data, &self.config).map_err(|_| HIPAAViolation::DeIdentificationFailure)?;

        // 3. Registrar acesso na trilha de auditoria
        self.audit.log_access("HIPAA", "Patient data accessed and de‑identified");

        Ok(deid)
    }

    /// Gera relatório de conformidade HIPAA
    pub fn generate_compliance_report(&self) -> HIPAAReport {
        HIPAAReport {
            deid_method: self.config.deid_method,
            access_audits: self.audit.query_hipaa_accesses(),
            violations: self.audit.query_violations("HIPAA"),
            status: ComplianceStatus::Compliant,
        }
    }
}

#[derive(Debug, thiserror::Error)]
pub enum HIPAAViolation {
    #[error("No valid consent on file")]
    NoConsent,
    #[error("Protected health information not properly de‑identified")]
    DeIdentificationFailure,
    #[error("Data accessed without authorization")]
    UnauthorizedAccess,
    #[error("Breach not reported within 60 days")]
    BreachNotificationFailure,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HIPAAReport {
    pub deid_method: DeIdentificationMethod,
    pub access_audits: Vec<AuditEntry>,
    pub violations: Vec<AuditEntry>,
    pub status: ComplianceStatus,
}
