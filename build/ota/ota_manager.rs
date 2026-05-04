// build/ota/ota_manager.rs — Sistema de atualização OTA com rollback e verificação
use anyhow::{Result, Context, bail};
use ed25519_dalek::{VerifyingKey, Signature};
use sha2::{Sha256, Digest};
use std::fs;
use std::path::{Path, PathBuf};
use tokio::io::AsyncWriteExt;
use tokio_stream::StreamExt;

use crate::core::config::OTAConfig;

/// Gerenciador de atualizações OTA com dual-slot e rollback
pub struct OTAManager {
    /// Configuração OTA
    config: OTAConfig,

    /// Chave pública para verificação de assinaturas
    public_key: VerifyingKey,

    /// Slots de boot: A (ativo) e B (inativo)
    slot_a: PathBuf,
    slot_b: PathBuf,

    /// Slot atualmente ativo
    active_slot: Slot,

    /// Estado da atualização em andamento
    update_in_progress: Option<UpdateState>,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Slot {
    A,
    B,
}

#[derive(Debug)]
pub struct UpdateState {
    target_slot: Slot,
    expected_hash: String,
    bytes_received: u64,
    total_bytes: u64,
    signature_verified: bool,
}

impl OTAManager {
    /// Criar novo gerenciador OTA
    pub fn new(config: OTAConfig, public_key: VerifyingKey) -> Result<Self> {
        let slot_a = config.slot_a_path.clone();
        let slot_b = config.slot_b_path.clone();

        // Determinar slot ativo atual via arquivo de marcação
        let active_slot = Self::detect_active_slot(&slot_a, &slot_b, &config.marker_path)?;

        Ok(Self {
            config,
            public_key,
            slot_a,
            slot_b,
            active_slot,
            update_in_progress: None,
        })
    }

    /// Detectar slot ativo atual
    fn detect_active_slot(slot_a: &Path, slot_b: &Path, marker: &Path) -> Result<Slot> {
        if marker.exists() {
            let content = fs::read_to_string(marker)?;
            match content.trim() {
                "A" => Ok(Slot::A),
                "B" => Ok(Slot::B),
                _ => bail!("Invalid slot marker content"),
            }
        } else {
            // Fallback: verificar qual slot tem binário válido
            if slot_a.join("arkhe-unified").exists() {
                Ok(Slot::A)
            } else if slot_b.join("arkhe-unified").exists() {
                Ok(Slot::B)
            } else {
                bail!("No valid slot found")
            }
        }
    }

    /// Iniciar download de atualização
    pub async fn start_update(
        &mut self,
        update_url: &str,
        expected_hash: &str,
        signature_base64: &str,
    ) -> Result<String> {
        if self.update_in_progress.is_some() {
            bail!("Update already in progress");
        }

        // Decodificar assinatura
        let sig_bytes = base64::decode(signature_base64)
            .context("Failed to decode signature")?;

        if sig_bytes.len() != 64 {
            bail!("Invalid signature length");
        }

        let signature = Signature::from_bytes(&sig_bytes.try_into().unwrap());

        // Verificar assinatura do hash esperado (não do binário inteiro para eficiência)
        self.public_key.verify(expected_hash.as_bytes(), &signature)
            .context("Signature verification failed")?;

        // Determinar slot alvo (o inativo)
        let target_slot = match self.active_slot {
            Slot::A => Slot::B,
            Slot::B => Slot::A,
        };

        let target_path = match target_slot {
            Slot::A => &self.slot_a,
            Slot::B => &self.slot_b,
        };

        // Iniciar download com verificação de hash em tempo real
        let update_id = format!("update_{}", chrono::Utc::now().timestamp());

        self.update_in_progress = Some(UpdateState {
            target_slot,
            expected_hash: expected_hash.to_string(),
            bytes_received: 0,
            total_bytes: 0,  // será atualizado via Content-Length
            signature_verified: true,
        });

        // Download em background (simplificado)
        let download_task = self.download_and_verify(
            update_url,
            target_path,
            expected_hash,
            update_id.clone(),
        );

        tokio::spawn(download_task);

        Ok(update_id)
    }

    /// Download com verificação de hash incremental
    async fn download_and_verify(
        &self,
        url: &str,
        target_path: &Path,
        expected_hash: &str,
        update_id: String,
    ) -> Result<()> {
        use reqwest::Client;

        let client = Client::new();
        let response = client.get(url).send().await
            .context("Failed to fetch update")?;

        let total_bytes = response.content_length().unwrap_or(0);

        /*// Atualizar estado
        if let Some(state) = &mut self.update_in_progress {
            state.total_bytes = total_bytes;
        }*/

        // Criar arquivo temporário
        let temp_path = target_path.join(format!(".update_{}.tmp", update_id));
        let mut file = tokio::fs::File::create(&temp_path).await
            .context("Failed to create temp file")?;

        // Hasher incremental
        let mut hasher = Sha256::new();
        let mut bytes_received = 0u64;

        // Stream download chunk por chunk
        let mut stream = response.bytes_stream();
        while let Some(chunk) = stream.next().await {
            let chunk = chunk.context("Failed to read chunk")?;

            // Atualizar hash
            hasher.update(&chunk);
            bytes_received += chunk.len() as u64;

            // Escrever no arquivo
            file.write_all(&chunk).await?;

            // Verificar progresso a cada 1MB
            if bytes_received % (1024 * 1024) == 0 {
                tracing::debug!("Download progress: {}/{} bytes", bytes_received, total_bytes);
            }
        }

        file.flush().await?;
        drop(file);

        // Verificar hash final
        let actual_hash = format!("{:x}", hasher.finalize());
        if actual_hash != expected_hash {
            // Limpar arquivo corrompido
            let _ = tokio::fs::remove_file(&temp_path).await;
            bail!("Hash mismatch: expected {}, got {}", expected_hash, actual_hash);
        }

        // Renomear para nome final
        let final_path = target_path.join("arkhe-unified");
        tokio::fs::rename(&temp_path, &final_path).await
            .context("Failed to finalize update")?;

        // Tornar executável
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mut perms = tokio::fs::metadata(&final_path).await?.permissions();
            perms.set_mode(0o755);
            tokio::fs::set_permissions(&final_path, perms).await?;
        }

        Ok(())
    }

    /// Commit da atualização (swap de slots)
    pub async fn commit_update(&mut self, update_id: &str) -> Result<()> {
        let state = self.update_in_progress.take()
            .ok_or_else(|| anyhow::anyhow!("No update in progress"))?;

        if !state.signature_verified {
            bail!("Cannot commit unverified update");
        }

        // Atualizar marker de slot ativo
        let new_active = match state.target_slot {
            Slot::A => "A",
            Slot::B => "B",
        };

        tokio::fs::write(&self.config.marker_path, new_active)
            .context("Failed to update slot marker")?;

        // Atualizar estado interno
        self.active_slot = state.target_slot;

        tracing::info!("✅ Update {} committed: now booting from slot {}",
                      update_id, new_active);

        Ok(())
    }

    /// Rollback para slot anterior em caso de falha de boot
    pub async fn rollback(&mut self) -> Result<()> {
        let previous_slot = match self.active_slot {
            Slot::A => Slot::B,
            Slot::B => Slot::A,
        };

        let previous_marker = match previous_slot {
            Slot::A => "A",
            Slot::B => "B",
        };

        // Verificar se slot anterior existe
        let previous_path = match previous_slot {
            Slot::A => &self.slot_a,
            Slot::B => &self.slot_b,
        };

        if !previous_path.join("arkhe-unified").exists() {
            bail!("Previous slot {} has no valid binary", previous_marker);
        }

        // Atualizar marker
        tokio::fs::write(&self.config.marker_path, previous_marker)
            .context("Failed to update slot marker for rollback")?;

        self.active_slot = previous_slot;

        tracing::warn!("🔄 Rollback to slot {} completed", previous_marker);

        Ok(())
    }

    /// Obter status da atualização atual
    pub fn get_update_status(&self) -> Option<UpdateStatus> {
        self.update_in_progress.as_ref().map(|state| UpdateStatus {
            target_slot: format!("{:?}", state.target_slot),
            expected_hash: state.expected_hash.clone(),
            bytes_received: state.bytes_received,
            total_bytes: state.total_bytes,
            progress: if state.total_bytes > 0 {
                (state.bytes_received as f64 / state.total_bytes as f64 * 100.0) as u8
            } else {
                0
            },
            signature_verified: state.signature_verified,
        })
    }

    /// Obter informações dos slots
    pub fn get_slot_info(&self) -> SlotInfo {
        SlotInfo {
            active_slot: format!("{:?}", self.active_slot),
            slot_a_exists: self.slot_a.join("arkhe-unified").exists(),
            slot_b_exists: self.slot_b.join("arkhe-unified").exists(),
            marker_path: self.config.marker_path.to_string_lossy().to_string(),
        }
    }
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct UpdateStatus {
    pub target_slot: String,
    pub expected_hash: String,
    pub bytes_received: u64,
    pub total_bytes: u64,
    pub progress: u8,  // 0-100
    pub signature_verified: bool,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct SlotInfo {
    pub active_slot: String,
    pub slot_a_exists: bool,
    pub slot_b_exists: bool,
    pub marker_path: String,
}
