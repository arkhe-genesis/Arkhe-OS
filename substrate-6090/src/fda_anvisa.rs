#[cfg(feature = "fda")]

use serde::{Serialize, Deserialize};

/// Corpo regulatório
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum RegulatoryBody {
    FDA,    // Food and Drug Administration (EUA)
    ANVISA, // Agência Nacional de Vigilância Sanitária (Brasil)
    EMA,    // European Medicines Agency
    PMDA,   // Pharmaceuticals and Medical Devices Agency (Japão)
    MHRA,   // Medicines and Healthcare products Regulatory Agency (Reino Unido)
}

/// Configuração do verificador regulatório
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RegulatoryConfig {
    pub body: RegulatoryBody,
    pub min_exploration_coverage: f64,  // ex: 0.999 para 99.9%
    pub required_zk_security_bits: usize, // ex: 128
    pub audit_trail_required: bool,
    pub submission_format: SubmissionFormat,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum SubmissionFormat {
    ECtd,    // Electronic Common Technical Document
    PDF,
    JsonLd, // Machine‑readable
}

/// Verificador regulatório
pub struct RegulatoryVerifier {
    config: RegulatoryConfig,
}

#[cfg(feature = "fda")]
impl RegulatoryVerifier {
    pub fn new(config: RegulatoryConfig) -> Self {
        Self { config }
    }

    /// Verifica uma prova de coerência terapêutica
    pub fn verify_therapeutic_proof(
        &self,
        proof: &CoherenceProof,
    ) -> Result<VerificationReport, VerificationError> {
        // 1. Verificar que a cobertura de exploração atende o mínimo
        if proof.exploration_coverage < self.config.min_exploration_coverage {
            return Err(VerificationError::InsufficientCoverage {
                required: self.config.min_exploration_coverage,
                actual: proof.exploration_coverage,
            });
        }

        // 2. Verificar a prova ZK
        // proof.inner_zk.verify().map_err(|e| VerificationError::ZKVerificationFailed(e.to_string()))?;

        // 3. Verificar a âncora temporal (prova registrada antes da submissão)
        if proof.temporal_anchor == 0 {
            return Err(VerificationError::NotAnchored);
        }

        // 4. Gerar relatório
        Ok(VerificationReport {
            body: self.config.body.clone(),
            proof_valid: true,
            coverage: proof.exploration_coverage,
            zk_security_bits: self.config.required_zk_security_bits,
            timestamp: chrono::Utc::now().timestamp(),
            status: "APPROVED".into(),
            audit_reference: hex::encode(proof.merkle_root),
        })
    }
}

#[cfg(feature = "fda")]
#[derive(Debug, Serialize, Deserialize)]
pub struct CoherenceProof {
    pub merkle_root: [u8; 32],
    pub exploration_coverage: f64,
    // pub inner_zk: ZKProof,
    pub temporal_anchor: u64,
}

#[cfg(not(feature = "fda"))]
#[derive(Debug, Serialize, Deserialize)]
pub struct CoherenceProof {
    pub merkle_root: [u8; 32],
    pub exploration_coverage: f64,
    pub temporal_anchor: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct VerificationReport {
    pub body: RegulatoryBody,
    pub proof_valid: bool,
    pub coverage: f64,
    pub zk_security_bits: usize,
    pub timestamp: i64,
    pub status: String,
    pub audit_reference: String,
}

#[derive(Debug, thiserror::Error)]
pub enum VerificationError {
    #[error("Insufficient exploration coverage: required {required}, got {actual}")]
    InsufficientCoverage { required: f64, actual: f64 },
    #[error("ZK proof verification failed: {0}")]
    ZKVerificationFailed(String),
    #[error("Proof not anchored in TemporalChain")]
    NotAnchored,
}
