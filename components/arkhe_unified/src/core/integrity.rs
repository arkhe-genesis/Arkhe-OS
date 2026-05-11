// src/core/integrity.rs — Verificação de integridade e assinatura digital
use anyhow::{Result, Context, bail};
use ed25519_dalek::{Verifier, VerifyingKey, Signature, SIGNATURE_LENGTH};
use sha2::{Sha256, Digest};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

use crate::core::config::Config;

/// Verificador de integridade para binário e módulos
pub struct IntegrityVerifier {
    /// Chave pública para verificação de assinaturas
    public_key: Option<VerifyingKey>,

    /// Manifesto de hashes esperado (gerado em build-time)
    expected_hashes: HashMap<String, String>,

    /// Caminho para binário principal
    binary_path: PathBuf,

    /// Modo estrito: falhar em qualquer discrepância
    strict_mode: bool,
}

impl IntegrityVerifier {
    /// Criar novo verificador com configuração
    pub fn new(config: &Config) -> Result<Self> {
        // Carregar chave pública se configurada
        let public_key = if let Some(key_path) = &config.security.public_key_path {
            let key_bytes = fs::read(key_path)
                .context(format!("Failed to read public key: {:?}", key_path))?;

            if key_bytes.len() != 32 {
                bail!("Invalid public key length: expected 32 bytes, got {}", key_bytes.len());
            }

            let key_array: [u8; 32] = key_bytes.try_into()
                .map_err(|_| anyhow::anyhow!("Failed to convert key bytes to array"))?;

            Some(VerifyingKey::from_bytes(&key_array)
                .context("Failed to parse Ed25519 public key")?)
        } else {
            None
        };

        // Carregar manifesto de hashes (gerado por build.rs)
        let expected_hashes = load_integrity_manifest()
            .context("Failed to load integrity manifest")?;

        // Determinar caminho do binário
        let binary_path = std::env::current_exe()
            .context("Failed to determine binary path")?;

        Ok(Self {
            public_key,
            expected_hashes,
            binary_path,
            strict_mode: config.security.strict_integrity,
        })
    }

    /// Verificar integridade de todos os módulos
    pub fn verify_all(&self) -> Result<IntegrityReport> {
        let mut report = IntegrityReport::new();

        // 1. Verificar hash do binário principal
        let binary_hash = compute_file_hash(&self.binary_path)?;
        if let Some(expected) = self.expected_hashes.get("arkhe-unified") {
            if binary_hash == *expected {
                report.add_check("binary", CheckStatus::Pass, None);
            } else {
                let msg = format!("Hash mismatch: expected {}, got {}", expected, binary_hash);
                report.add_check("binary", CheckStatus::Fail, Some(msg.clone()));
                if self.strict_mode {
                    bail!("{}", msg);
                }
            }
        } else {
            report.add_check("binary", CheckStatus::Warning, Some("No expected hash in manifest".into()));
        }

        // 2. Verificar hashes dos módulos de substrato
        let substrate_dir = self.binary_path.parent()
            .map(|p| p.join("substrates"))
            .filter(|p| p.exists());

        if let Some(dir) = substrate_dir {
            for entry in fs::read_dir(&dir).context("Failed to read substrates directory")? {
                let entry = entry?;
                let path = entry.path();

                if path.extension().map_or(false, |ext| ext == "so" || ext == "dylib" || ext == "dll") {
                    let module_name = path.file_name()
                        .and_then(|n| n.to_str())
                        .unwrap_or("unknown");

                    let hash = compute_file_hash(&path)?;
                    if let Some(expected) = self.expected_hashes.get(module_name) {
                        if hash == *expected {
                            report.add_check(module_name, CheckStatus::Pass, None);
                        } else {
                            let msg = format!("Module {} hash mismatch", module_name);
                            report.add_check(module_name, CheckStatus::Fail, Some(msg.clone()));
                            if self.strict_mode {
                                bail!("{}", msg);
                            }
                        }
                    }
                }
            }
        }

        // 3. Verificar assinatura digital do binário (se chave disponível)
        if let Some(pubkey) = &self.public_key {
            let sig_path = self.binary_path.with_extension("sig");
            if sig_path.exists() {
                match verify_binary_signature(&self.binary_path, &sig_path, pubkey) {
                    Ok(_) => report.add_check("signature", CheckStatus::Pass, None),
                    Err(e) => {
                        report.add_check("signature", CheckStatus::Fail, Some(e.to_string()));
                        if self.strict_mode {
                            bail!("Signature verification failed: {}", e);
                        }
                    }
                }
            } else {
                report.add_check("signature", CheckStatus::Warning, Some("No signature file found".into()));
            }
        }

        // 4. Verificar integridade de configuração
        // omitted

        Ok(report)
    }

    /// Gerar relatório detalhado de integridade
    pub fn generate_report(&self, signature_path: Option<&Path>) -> Result<IntegrityReport> {
        let mut report = self.verify_all()?;

        // Adicionar metadados ao relatório
        report.metadata.insert("binary_path".into(), self.binary_path.display().to_string().into());
        report.metadata.insert("strict_mode".into(), self.strict_mode.into());
        report.metadata.insert("public_key_loaded".into(), self.public_key.is_some().into());
        report.metadata.insert("manifest_entries".into(), self.expected_hashes.len().into());

        // Se caminho de assinatura fornecido, verificar explicitamente
        if let Some(sig_path) = signature_path {
            if let Some(pubkey) = &self.public_key {
                match verify_binary_signature(&self.binary_path, sig_path, pubkey) {
                    Ok(_) => {
                        report.metadata.insert("external_signature".into(), "valid".into());
                    }
                    Err(e) => {
                        report.metadata.insert("external_signature".into(), format!("invalid: {}", e).into());
                    }
                }
            }
        }

        Ok(report)
    }
}

/// Relatório de verificação de integridade
#[derive(Debug, Clone, serde::Serialize)]
pub struct IntegrityReport {
    #[serde(with = "chrono::serde::ts_seconds")]
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub checks: Vec<CheckResult>,
    pub overall_status: ReportStatus,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct CheckResult {
    pub component: String,
    pub status: CheckStatus,
    pub message: Option<String>,
    #[serde(with = "chrono::serde::ts_seconds")]
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CheckStatus {
    Pass,
    Warning,
    Fail,
}

#[derive(Debug, Clone, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReportStatus {
    AllPassed,
    Warnings,
    Failed,
}

impl IntegrityReport {
    fn new() -> Self {
        Self {
            timestamp: chrono::Utc::now(),
            checks: Vec::new(),
            overall_status: ReportStatus::AllPassed,
            metadata: HashMap::new(),
        }
    }

    fn add_check(&mut self, component: &str, status: CheckStatus, message: Option<String>) {
        self.checks.push(CheckResult {
            component: component.to_string(),
            status: status.clone(),
            message,
            timestamp: chrono::Utc::now(),
        });

        // Update overall status
        if status == CheckStatus::Fail {
            self.overall_status = ReportStatus::Failed;
        } else if status == CheckStatus::Warning && self.overall_status == ReportStatus::AllPassed {
            self.overall_status = ReportStatus::Warnings;
        }
    }
}

/// Computar hash SHA-256 de arquivo
fn compute_file_hash(path: &Path) -> Result<String> {
    let mut file = fs::File::open(path)
        .context(format!("Failed to open file: {:?}", path))?;

    let mut hasher = Sha256::new();
    std::io::copy(&mut file, &mut hasher)
        .context("Failed to read file for hashing")?;

    Ok(format!("{:x}", hasher.finalize()))
}

/// Carregar manifesto de integridade gerado em build-time
fn load_integrity_manifest() -> Result<HashMap<String, String>> {
    // O manifesto é embutido no binário via include_str! ou lido de arquivo adjacente
    // Para exemplo: tentar ler arquivo adjacente primeiro, depois fallback para embutido

    let binary_path = std::env::current_exe()?;
    let manifest_path = binary_path.parent()
        .map(|p| p.join("integrity_manifest.json"))
        .filter(|p| p.exists());

    let manifest_content = if let Some(path) = manifest_path {
        fs::read_to_string(&path)
            .context(format!("Failed to read manifest: {:?}", path))?
    } else {
        // Fallback: manifesto embutido (gerado por build.rs via include_str)
        // Para exemplo, retornar mapa vazio
        return Ok(HashMap::new());
    };

    serde_json::from_str(&manifest_content)
        .context("Failed to parse integrity manifest JSON")
}

/// Verificar assinatura digital do binário
fn verify_binary_signature(
    binary_path: &Path,
    signature_path: &Path,
    public_key: &VerifyingKey,
) -> Result<()> {
    // Ler binário e computar hash
    let binary_hash = compute_file_hash(binary_path)?;

    // Ler assinatura
    let sig_bytes = fs::read(signature_path)
        .context(format!("Failed to read signature: {:?}", signature_path))?;

    if sig_bytes.len() != SIGNATURE_LENGTH {
        bail!("Invalid signature length: expected {}, got {}", SIGNATURE_LENGTH, sig_bytes.len());
    }

    let signature = Signature::from_bytes(&sig_bytes.try_into()
        .map_err(|_| anyhow::anyhow!("Failed to convert signature bytes"))?);

    // Verificar: assinatura deve ser sobre o hash do binário
    public_key.verify(binary_hash.as_bytes(), &signature)
        .context("Ed25519 signature verification failed")?;

    Ok(())
}
