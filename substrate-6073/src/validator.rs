use crate::types::SignedManifest;
use hmac::{Hmac, Mac};
use sha2::{Digest, Sha256};
use std::collections::HashMap;

type HmacSha256 = Hmac<Sha256>;

/// Erros possíveis durante validação
#[derive(Debug, thiserror::Error)]
pub enum ValidationError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Algorithm not supported: {0}")]
    UnsupportedAlgorithm(String),
    #[error("HMAC verification failed")]
    HmacMismatch,
    #[error("Manifest SHA256 mismatch")]
    ManifestHashMismatch,
    #[error("File integrity error: {0} (expected {1}, got {2})")]
    FileIntegrityError(String, String, String),
    #[error("Missing file: {0}")]
    MissingFile(String),
}

/// Validador principal
pub struct FinancialValidator {
    /// Chaves pré‑compartilhadas (key_label -> bytes)
    keys: HashMap<String, Vec<u8>>,
}

impl FinancialValidator {
    /// Cria um validador com as chaves fornecidas.
    /// Em produção, as chaves são carregadas de um HSM ou cofre criptográfico.
    pub fn new(keys: HashMap<String, Vec<u8>>) -> Self {
        Self { keys }
    }

    /// Valida completamente um SignedManifest:
    /// 1. Verifica a assinatura HMAC do manifesto.
    /// 2. Verifica o hash do manifesto (manifest_sha256).
    /// 3. Para cada arquivo listado, verifica seu hash SHA256 (se os bytes do arquivo forem fornecidos).
    pub fn validate(
        &self,
        signed: &SignedManifest,
        file_contents: &HashMap<String, Vec<u8>>, // caminho -> bytes
    ) -> Result<(), ValidationError> {
        // 1. Verificar algoritmo
        if signed.algorithm != "HMAC-SHA256" {
            return Err(ValidationError::UnsupportedAlgorithm(
                signed.algorithm.clone(),
            ));
        }

        // 2. Converter manifesto para bytes (canônicos) e recalcular SHA256
        let manifest_json = serde_json::to_vec(&signed.manifest)
            .map_err(|e| ValidationError::Io(std::io::Error::new(std::io::ErrorKind::Other, e)))?;
        let computed_manifest_hash = sha2::Sha256::digest(&manifest_json);
        let computed_manifest_hex = hex::encode(computed_manifest_hash);

        if computed_manifest_hex.to_uppercase() != signed.manifest_sha256.to_uppercase() {
            return Err(ValidationError::ManifestHashMismatch);
        }

        // 3. Verificar assinatura HMAC do manifesto
        let key = self.keys.get(&signed.key_label).ok_or_else(|| {
            ValidationError::UnsupportedAlgorithm(format!("key not found: {}", signed.key_label))
        })?;

        let mut mac = HmacSha256::new_from_slice(key)
            .map_err(|_| ValidationError::UnsupportedAlgorithm("invalid key".into()))?;
        mac.update(&manifest_json);
        let tag = mac.finalize().into_bytes();
        let tag_hex = hex::encode(tag);

        if tag_hex.to_uppercase() != signed.signature.to_uppercase() {
            return Err(ValidationError::HmacMismatch);
        }

        // 4. Verificar integridade dos arquivos (se fornecidos)
        for file_entry in &signed.manifest.files {
            if let Some(content) = file_contents.get(&file_entry.file) {
                let computed_file_hash = sha2::Sha256::digest(content);
                let computed_file_hex = hex::encode(computed_file_hash);

                if computed_file_hex.to_uppercase() != file_entry.sha256.to_uppercase() {
                    return Err(ValidationError::FileIntegrityError(
                        file_entry.file.clone(),
                        file_entry.sha256.clone(),
                        computed_file_hex,
                    ));
                }
            } else {
                // Se não temos o conteúdo, retornamos erro ou apenas pulamos?
                // Aqui exigimos os arquivos para validação completa.
                return Err(ValidationError::MissingFile(file_entry.file.clone()));
            }
        }

        Ok(())
    }
}
