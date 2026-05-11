use crate::QArtConfig;
use crate::types::*;
use crate::QArtError;
use crate::influence::compute_influence_probability;
use crate::fingerprint::extract_art_fingerprint;
use crate::temporal::ArtBlockRegistry;
use crate::compensation::calculate_royalties;
use crate::provenance::ZKProofSystem;
use crate::provenance::build_influence_merkle_root;
use tracing::{debug, info, warn, error};
use std::sync::Arc;
use sha3::Digest;
use crate::DEFAULT_INFLUENCE_WINDOW_SECONDS;

/// Motor principal do Q-Art — Orquestra todo o pipeline
pub struct QArtEngine {
    pub config: QArtConfig,
    block_registry: Arc<ArtBlockRegistry>,
    zk_system: Option<ZKProofSystem>,
}

impl QArtEngine {
    pub fn new(config: QArtConfig, block_registry: Arc<ArtBlockRegistry>) -> Self {
        let zk_system = if config.enable_zk_proofs {
            Some(ZKProofSystem::new(true))
        } else {
            None
        };

        Self { config, block_registry, zk_system }
    }

    /// 1. Registra obra original
    pub fn register_original_work(
        &self,
        raw_data: &[u8],
        orcid_id: Option<OrcidId>,
    ) -> Result<ArtFingerprint, QArtError> {
        let fingerprint = extract_art_fingerprint(
            raw_data, &self.config.style_model, orcid_id.clone(),
        )?;
        self.block_registry.anchor_fingerprint(&fingerprint)?;

        info!(
            orcid = ?orcid_id,
            raw_hash = hex::encode(&fingerprint.raw_hash[..8]),
            "Original work registered"
        );

        Ok(fingerprint)
    }

    /// 2. Processa bloco artístico e calcula royalties
    pub async fn process_new_art_block(
        &self,
        block: &ArtBlock,
    ) -> Result<Vec<RoyaltyEvent>, QArtError> {
        let window_seconds = DEFAULT_INFLUENCE_WINDOW_SECONDS;
        let candidates = self.block_registry.query_fingerprints_since(
            block.timestamp.saturating_sub(window_seconds),
        )?;

        debug!(
            block_number = block.block_id.len(),
            candidates = candidates.len(),
            "Processing art block with influence candidates"
        );

        let zk_enabled = self.zk_system.is_some();
        let network_fee = self.config.network_fee;
        let use_reputation = self.config.use_orcid_reputation;
        let min_prob = self.config.min_influence_probability;

        let mut royalties = Vec::new();
        let mut merkle_links: Vec<ProvenanceLink> = Vec::new();
        let mut zk_proofs: Vec<(Vec<u8>, Vec<u8>)> = Vec::new(); // (proof, deposit_id)

        for src_fp in &candidates {
            let prob = compute_influence_probability(
                src_fp, block, &self.block_registry,
            )?;

            if prob < min_prob {
                continue;
            }

            let Some(orcid) = &src_fp.origin_orcid else { continue; };

            let amount = calculate_royalties(
                prob, block.economic_value, network_fee, orcid, use_reputation,
            )?;

            let pix_key = self.resolve_orcid_to_pix(orcid)?;

            // Se ZK habilitado, gerar prova
            if zk_enabled {
                if let Some(zk) = &self.zk_system {
                    match zk.generate_style_influence(
                        &src_fp.style_embedding.vector,
                        &block.fingerprint.style_embedding.vector,
                        prob,
                    ) {
                        Ok(proof) => {
                            let deposit_id = self.escrow_deposit(
                                orcid, amount, &proof,
                            ).await?;
                            zk_proofs.push((proof.proof_bytes, deposit_id));
                        }
                        Err(e) => {
                            warn!(orcid = %orcid, error = %e, "ZK proof generation failed");
                        }
                    }
                }
            }

            merkle_links.push(ProvenanceLink {
                source_fingerprint: src_fp.clone(),
                influence_probability: prob,
                proof: zk_proofs.last().map(|p| p.0.clone()),
            });

            royalties.push(RoyaltyEvent {
                target_block_id: block.block_id.clone(),
                source_orcid: orcid.to_string(),
                source_fingerprint: src_fp.clone(),
                amount,
                pix_key,
                timestamp: chrono::Utc::now().timestamp() as u64,
            });
        }

        // Construir Merkle root das influências
        let _merkle_root = build_influence_merkle_root(&merkle_links);

        // Pagar royalties via bridge
        for event in &royalties {
            if let Err(e) = self.pay_royalty(event).await {
                error!(
                    orcid = %event.source_orcid,
                    amount = event.amount,
                    error = %e,
                    "Failed to send royalty payment"
                );
            }
        }

        info!(
            block_number = block.block_id.len(),
            royalties_count = royalties.len(),
            total_amount = royalties.iter().map(|r| r.amount).sum::<f64>(),
            "Art block processed"
        );

        Ok(royalties)
    }

    /// Resolver chave Pix a partir do ORCID
    fn resolve_orcid_to_pix(&self, orcid: &str) -> Result<String, QArtError> {
        // Em produção: consultar mapeamento ORCID→Pix via ORCID API
        // Ou usar a bridge x402 para criar cobrança diretamente
        Ok(format!("pix-{}", &orcid[..8]))
    }

    /// Criar depósito escrow para royalty
    #[cfg(feature = "x402-payments")]
    async fn escrow_deposit(
        &self,
        _orcid: &str,
        _amount: f64,
        _proof: &crate::types::ZKProof,
    ) -> Result<Vec<u8>, QArtError> {
        // Gerar ID do depósito
        let mut hasher = sha3::Sha3_256::new();
        hasher.update(format!("{}{:?}{}", _orcid, _amount, chrono::Utc::now().timestamp_nanos_opt().unwrap_or(0)).as_bytes());
        let deposit_id = hasher.finalize();
        Ok(deposit_id.to_vec())
    }

    #[cfg(not(feature = "x402-payments"))]
    async fn escrow_deposit(
        &self,
        _orcid: &str,
        _amount: f64,
        _proof: &crate::types::ZKProof,
    ) -> Result<Vec<u8>, QArtError> {
        Ok(vec![])
    }

    /// Executar pagamento do royalty
    async fn pay_royalty(&self, event: &RoyaltyEvent) -> Result<(), QArtError> {
        #[cfg(feature = "x402-payments")]
        {
            let bridge = crate::compensation::X402Bridge::new(
                crate::compensation::PixX402Config::default(),
            );
            bridge.start_health_checks();
            bridge.send_royalty_sync(event)?;
        }

        #[cfg(not(feature = "x402-payments"))]
        {
            let _ = event;
            info!("x402-payments disabled — royalty simulated");
        }

        Ok(())
    }

    pub async fn process_new_art_block_auto(
        &self,
        block: &ArtBlock,
        bridge: &Arc<crate::compensation::X402Bridge>,
    ) -> Vec<RoyaltyEvent> {
        let events = self.process_new_art_block(block).await.unwrap_or_default();
        for event in &events {
            if let Err(e) = bridge.send_royalty_sync(event) {
                tracing::error!("Falha ao pagar royalty: {}", e);
            }
        }
        events
    }
}
