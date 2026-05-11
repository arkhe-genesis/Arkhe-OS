// ============================================================================
// ARKHE Ω‑TEMP v6.1.0 — Substrato 6090: Full Compliance Engine
// ============================================================================
//
// ═══════════════════════════════════════════════════════════════════════════
//  CAMADA TRANSVERSAL DE CONFORMIDADE REGULATÓRIA
// ═══════════════════════════════════════════════════════════════════════════
//
// O Compliance Engine garante que cada operação da ARKHE — desde uma
// simulação celular até um pagamento Pix — esteja em conformidade com
// as regulações globais:
//
//   - HIPAA (EUA)          → proteção de dados de saúde
//   - GDPR (UE)            → privacidade e direito ao esquecimento
//   - LGPD (Brasil)        → proteção de dados pessoais
//   - FDA / ANVISA         → verificação de provas terapêuticas
//   - KYC / AML            → prevenção à lavagem de dinheiro
//   - FAIR Principles      → integridade e reutilização de dados
//   - ISO 27001 / SOC 2    → segurança da informação
//
// Cada verificação de conformidade é registrada como um bloco na
// TemporalChain, gerando um trilha de auditoria imutável.
//
// Exemplo de uso:
//   use arkhe_compliance::{
//       ComplianceEngine, HIPAACompliance, GDPRCompliance,
//       RegulatoryVerifier, KYCChecker, AuditTrail,
//   };
//
//   let engine = ComplianceEngine::new(config)
//       .with_hipaa(hipaa_config)
//       .with_gdpr(gdpr_config)
//       .with_fda_verifier(fda_config)
//       .launch()?;
//
//   // Antes de processar um dado de paciente:
//   engine.verify_patient_data(&cell_data)?;
//
// ============================================================================

#![allow(clippy::too_many_arguments)]

// ============================================================================
// MÓDULOS
// ============================================================================

pub mod hipaa;
pub mod gdpr;
pub mod lgpd;
pub mod fda_anvisa;
pub mod kyc_aml;
pub mod fair;
pub mod iso_soc;
pub mod audit;
pub mod consent;
pub mod anonymization;
pub mod verification;
pub mod temporal_anchor;

// ============================================================================
// RE‑EXPORTS
// ============================================================================

pub use hipaa::{
    HIPAACompliance, HIPAAViolation, HIPAAReport,
    DeIdentificationMethod, HIPAAConfig,
};

pub use gdpr::{
    GDPRCompliance, GDPRRequest, GDPRRight, GDPRResponse, GDPRViolation
};

pub use lgpd::{
    LGPDCompliance, LGPDRequest, LGPDRight,
};

pub use fda_anvisa::{
    RegulatoryVerifier, CoherenceProof, VerificationReport,
    RegulatoryConfig, RegulatoryBody,
};

pub use kyc_aml::{
    KYCChecker, KYCStatus, AMLReport, PixTransaction,
};

pub use fair::{
    FAIRValidator, FAIRMetrics,
};

pub use iso_soc::{
    ISOSOCCompliance, SecurityAudit, SOC2Report,
    AccessControlAudit, EncryptionAudit,
};

pub use audit::{
    AuditTrail, AuditEntry, AuditLevel,
    ComplianceReport, ComplianceStatus,
};

pub use consent::{
    ConsentManager, ConsentRecord,
    ConsentType, PHIPolicy,
};

pub use anonymization::{
    AnonymizationEngine,
    PHIField, DeIdentifiedData, PHIType, AnonymizationError,
};

pub use verification::{
    ComplianceVerifier, VerificationResult,
    BatchVerifier,
};

pub use temporal_anchor::{
    ComplianceBlock, ComplianceEvent,
    anchor_compliance_event,
};
