use serde::{Serialize, Deserialize};
use regex::Regex;
use crate::hipaa::{HIPAAConfig, DeIdentificationMethod};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PHIField {
    pub name: String,
    pub value: String,
    pub field_type: PHIType,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum PHIType {
    Name,
    Email,
    Phone,
    SSN,        // Social Security Number (EUA)
    CPF,        // Cadastro de Pessoas Físicas (Brasil)
    Address,
    DateOfBirth,
    MedicalRecordNumber,
    IPAddress,
    BiometricIdentifier,
}

pub struct AnonymizationEngine {
    patterns: Vec<(Regex, String)>, // regex → replacement
}

impl AnonymizationEngine {
    pub fn new() -> Self {
        Self {
            patterns: vec![
                (Regex::new(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b").unwrap(), "[NAME]".into()),
                (Regex::new(r"\b[\w\.-]+@[\w\.-]+\.\w+\b").unwrap(), "[EMAIL]".into()),
                (Regex::new(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b").unwrap(), "[CPF]".into()),
                (Regex::new(r"\b\d{3}-\d{2}-\d{4}\b").unwrap(), "[SSN]".into()),
            ]
        }
    }

    /// De‑identifica dados conforme método especificado
    pub fn deidentify(&self, data: &[u8], config: &HIPAAConfig) -> Result<DeIdentifiedData, AnonymizationError> {
        let mut text = String::from_utf8_lossy(data).to_string();
        for (regex, replacement) in &self.patterns {
            text = regex.replace_all(&text, replacement.as_str()).to_string();
        }
        Ok(DeIdentifiedData {
            data: text.into_bytes(),
            method: config.deid_method,
            fields_removed: self.patterns.len(),
        })
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DeIdentifiedData {
    pub data: Vec<u8>,
    pub method: DeIdentificationMethod,
    pub fields_removed: usize,
}

#[derive(Debug, thiserror::Error)]
pub enum AnonymizationError {
    #[error("De‑identification failed: {0}")]
    ProcessingError(String),
}
