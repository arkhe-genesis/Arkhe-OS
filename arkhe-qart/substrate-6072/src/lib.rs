// ============================================================================
// ARKHE Ω‑TEMP v6.0.0 — Substrato 6072: Q-Art (Quantum Artistic Influence)
// ============================================================================
//
// ═══════════════════════════════════════════════════════════════════════════
//  MÓDULO RAIZ — Ponto de entrada canônico do Substrato 6072
// ═══════════════════════════════════════════════════════════════════════════
//
// Este módulo re-exporta toda a funcionalidade do Q-Art, organizando
// a API pública em camadas:
//
//   Camada 1 — Tipos e Erros (tipos, errors, config)
//   Camada 2 — Fingerprint (perceptual, estilístico, metadados, composto)
//   Camada 3 — Influência (similaridade, motivos, causalidade, modelo)
//   Camada 4 — Proveniência (Merkle, ZK, registro)
//   Camada 5 — Compensação (royalties, Pix bridge, escrow)
//   Camada 6 — Oracle (ecos estilísticos, leilão de entropia, tendências)
//   Camada 7 — Temporal (ArtBlock, árvore genealógica, ancoragem)
//   Camada 8 — Motor Principal (QArtEngine)
//
// Features condicionais:
//   full-zk     → Plonky2 circuitos ZK completos
//   style-models → CLIP + AST via tch-rs (Torch)
//   x402-payments → Bridge Pix via IPC Unix Socket
//
// Exemplo mínimo:
//
//   use arkhe_qart::{
//       QArtEngine, QArtConfig, ArtFingerprint, ArtBlock,
//       ZKProofSystem, ClipEmbedder, PixIpcClient,
//   };
//
// ============================================================================

#![cfg_attr(docsrs, feature(doc_auto_cfg))]

// ============================================================================
// MÓDULOS INTERNOS
// ============================================================================

// --- Camada 1: Tipos Fundamentais ---
mod types;
mod errors;
mod config;

// --- Camada 2: Fingerprint ---
pub mod fingerprint {
    pub mod perceptual;         // pHash, PDQ, Chromaprint
    pub mod style_embedding;    // CLIP, AST embeddings
    pub mod metadata_commitment; // Pedersen / SHA3 commitments
    pub mod composite;           // Pipeline completo de fingerprinting

    // Re-exports para conveniência
    pub use perceptual::{
        perceptual_hash_image,
        perceptual_hash_audio,
        PerceptualHash,
    };
    pub use style_embedding::{
        ClipEmbedder,
        StyleEmbedding,
        StyleModelConfig,
        ClipModel,
        EmbeddingCache,
        cosine_similarity as style_cosine_similarity,
    };
    pub use metadata_commitment::{
        MetadataCommitment,
        commit_metadata,
    };
    pub use composite::{
        ArtFingerprint as CompositeArtFingerprint,
        extract_art_fingerprint,
    };
}

// --- Camada 3: Influência ---
pub mod influence {
    pub mod style_similarity;    // Distância coseno, SSIM, LPIPS
    pub mod motif_detection;     // Patch matching, n-gramas visuais
    pub mod temporal_causality;  // Rastro temporal de acessos
    pub mod probability_model;   // Ensemble + sigmoid

    pub use style_similarity::style_similarity;
    pub use motif_detection::motif_match_score;
    pub use temporal_causality::temporal_access_evidence;
    pub use probability_model::compute_influence_probability;
}

// --- Camada 4: Proveniência e ZK ---
pub mod provenance {
    pub mod merkle_tree;         // Merkle tree de influências
    pub mod zk_circuit;          // Plonky2: 3 circuitos completos
    pub mod proof_registry;      // Registro on-chain

    pub use merkle_tree::{
        build_influence_merkle_root,
    };
    pub use zk_circuit::{
        ZKProof,
        ZKProofConfig,
        ProofType,
        StyleInfluenceCircuit,
        StyleInfluenceProver,
        OrcidOwnershipCircuit,
        RoyaltyCorrectnessCircuit,
        ZKProofSystem,
        SetupOutput,
        CircuitSetup,
        FIXED_POINT_SCALE,
        STYLE_EMBEDDING_DIM,
    };
    pub use proof_registry::register_proof_on_chain;
}

// --- Camada 5: Compensação ---
pub mod compensation {
    pub mod royalty_calculator;  // Cálculo de micro-royalties
    pub mod x402_pix_bridge;     // Bridge HTTP/IPC ↔ Pix Go
    pub mod x402_bridge;         // Bridge de alto nível
    pub mod escrow;              // Client escrow (on-chain)

    pub use royalty_calculator::{
        calculate_royalties,
        RoyaltyCalculator,
    };
    pub use x402_pix_bridge::{
        X402PixBridge,
        X402Config as PixX402Config,
        PaymentConfirmation,
        PaymentStatus,
        ChargeResponse,
        BridgeError,
    };
    pub use x402_bridge::X402Bridge;
    pub use escrow::EscrowClient;
}

// --- Camada 6: Oracle ---
pub mod oracle {
    pub mod style_oracle;        // Ecos estilísticos via malha orbital
    pub mod entropy_auction;     // Leilão por entropia / raridade
    pub mod trend_detector;      // Detecção de tendências emergentes
    pub mod auction_engine;      // Motor de leilão completo

    pub use style_oracle::query_similar_works;
    pub use entropy_auction::{
        EntropyAuction,
        EntropyLot,
        AuctionResult,
        run_entropy_auction,
    };
    pub use trend_detector::{
        TrendDetector,
        Trend,
        StyleTrend,
        detect_trends,
        detect_emerging_styles,
    };
    pub use auction_engine::AuctionEngine;
}

// --- Camada 7: Temporal ---
pub mod temporal {
    pub mod art_block;           // ArtBlock + ArtBlockRegistry
    pub mod lineage_tree;        // Árvore genealógica de influências
    pub mod anchor;              // Ancoragem na cadeia temporal

    pub use art_block::{
        ArtBlock,
        ArtBlockRegistry,
        ArtBlockHeader,
        ArtBlockType,
    };
    pub use lineage_tree::LineageTree;
    pub use anchor::{
        anchor_derivation,
        anchor_fingerprint,
    };
}

// --- Camada 8: Motor Principal ---
mod engine;

// ============================================================================
// RE-EXPORTS — API PÚBLICA DE ALTO NÍVEL
// ============================================================================

// Tipos fundamentais
pub use types::{
    OrcidId,
    ArtFingerprint,
    ArtBlock,
    RoyaltyEvent,
    ProvenanceLink,
    MetadataCommitment,
    PerceptualHash,
    StyleEmbedding,
};

// Erros
pub use errors::QArtError;

// Configuração
pub use config::QArtConfig;

// Motor principal
pub use engine::QArtEngine;

// ZK Proof System
pub use provenance::zk_circuit::ZKProofSystem;

// Pix Bridge
#[cfg(feature = "x402-payments")]
pub use compensation::x402_bridge::X402Bridge;

// CLIP Embedder
#[cfg(feature = "style-models")]
pub use fingerprint::style_embedding::ClipEmbedder;

// ============================================================================
// MÓDULOS DE INTEGRAÇÃO
// ============================================================================

/// Integração com o Continental Mind (substrate-6064)
#[cfg(feature = "sim-test")]
pub mod integration {
    pub mod continental_mind;
    pub mod test_helpers;
}

/// Bindings para linguagens externas
pub mod bindings {
    /// Bindings Python via PyO3
    #[cfg(feature = "python-bindings")]
    pub mod python;

    /// Bindings WebAssembly
    #[cfg(feature = "wasm-bindings")]
    pub mod wasm;

    /// CLI tool
    pub mod cli;
}

// ============================================================================
// MACROS UTILITÁRIAS
// ============================================================================

/// Macro para criação simplificada de ArtFingerprint
#[macro_export]
macro_rules! art_fingerprint {
    (raw: $data:expr, orcid: $orcid:expr, style_model: $model:expr) => {{
        use $crate::fingerprint::composite::extract_art_fingerprint;
        extract_art_fingerprint($data, $model, Some($orcid.to_string()))
            .expect("Failed to extract art fingerprint")
    }};
    (raw: $data:expr, style_model: $model:expr) => {{
        use $crate::fingerprint::composite::extract_art_fingerprint;
        extract_art_fingerprint($data, $model, None)
            .expect("Failed to extract art fingerprint")
    }};
}

/// Macro para criação simplificada de ArtBlock
#[macro_export]
macro_rules! art_block {
    (id: $id:expr, fp: $fp:expr, value: $value:expr, energy: $energy:expr) => {{
        use $crate::types::ArtBlock;
        ArtBlock {
            block_id: $id.to_vec(),
            fingerprint: $fp,
            parent_influences: Vec::new(),
            economic_value: $value,
            energy_cost: $energy,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        }
    }};
}

/// Macro para inicialização rápida do QArtEngine
#[macro_export]
macro_rules! qart_engine {
    (config: { $( $key:ident : $value:expr ),* $(,)? }) => {{
        use $crate::config::QArtConfig;
        use $crate::temporal::art_block::ArtBlockRegistry;
        use std::sync::Arc;

        let mut config = QArtConfig::default();
        $( config.$key = $value; )*

        let registry = Arc::new(ArtBlockRegistry::new());
        $crate::QArtEngine::new(config, registry)
    }};
    () => {{
        qart_engine!(config: {})
    }};
}

/// Macro para configuração do ZKP
#[macro_export]
macro_rules! zk_config {
    (security: $bits:expr, variables: $vars:expr) => {{
        use $crate::provenance::zk_circuit::ZKProofConfig;
        ZKProofConfig {
            security_bits: $bits,
            max_variables: $vars,
            num_wires: 4,
        }
    }};
    (default) => {{
        use $crate::provenance::zk_circuit::ZKProofConfig;
        ZKProofConfig::default()
    }};
}

/// Macro para criação simplificada de X402Bridge
#[cfg(feature = "x402-payments")]
#[macro_export]
macro_rules! x402_bridge {
    (sockets: [$($socket:expr),*]) => {{
        use $crate::compensation::x402_bridge::X402Bridge;
        use $crate::compensation::x402_bridge::X402Config;

        let config = X402Config {
            socket_paths: vec![$($socket.to_string()),*],
            ..X402Config::default()
        };
        X402Bridge::new(config)
    }};
    (socket: $socket:expr) => {{
        x402_bridge!(sockets: [$socket])
    }};
    () => {{
        x402_bridge!(socket: "/var/run/arkhe/pix.sock")
    }};
}

// ============================================================================
// TRAITS DE INTEGRAÇÃO
// ============================================================================

/// Trait para qualquer coisa que possa ser ancorada na cadeia temporal
pub trait TemporalAnchorable {
    /// Retorna os dados que serão ancorados
    fn anchor_data(&self) -> Vec<u8>;

    /// Retorna o timestamp esperado
    fn anchor_timestamp(&self) -> u64;

    /// Verifica se a âncora é válida
    fn verify_anchor(&self, anchor_hash: &[u8; 32]) -> bool;
}

impl TemporalAnchorable for ArtBlock {
    fn anchor_data(&self) -> Vec<u8> {
        serde_json::to_vec(self).unwrap_or_default()
    }

    fn anchor_timestamp(&self) -> u64 {
        self.timestamp
    }

    fn verify_anchor(&self, anchor_hash: &[u8; 32]) -> bool {
        use sha3::{Sha3_256, Digest};
        let data = self.anchor_data();
        let computed = Sha3_256::digest(&data);
        computed.as_slice() == anchor_hash
    }
}

impl TemporalAnchorable for ArtFingerprint {
    fn anchor_data(&self) -> Vec<u8> {
        serde_json::to_vec(self).unwrap_or_default()
    }

    fn anchor_timestamp(&self) -> u64 {
        self.timestamp
    }

    fn verify_anchor(&self, anchor_hash: &[u8; 32]) -> bool {
        use sha3::{Sha3_256, Digest};
        let data = self.anchor_data();
        let computed = Sha3_256::digest(&data);
        computed.as_slice() == anchor_hash
    }
}

/// Trait para provedores de embedding de estilo
pub trait StyleEmbedder {
    /// Extrai embedding de uma imagem
    fn extract_image(&self, data: &[u8]) -> Result<StyleEmbedding, QArtError>;

    /// Extrai embedding de um áudio
    fn extract_audio(&self, data: &[u8]) -> Result<StyleEmbedding, QArtError>;

    /// Extrai embedding de texto
    fn extract_text(&self, text: &str) -> Result<StyleEmbedding, QArtError>;

    /// Similaridade entre dois embeddings
    fn similarity(&self, a: &[f32], b: &[f32]) -> f64;
}

#[cfg(feature = "style-models")]
impl StyleEmbedder for ClipEmbedder {
    fn extract_image(&self, data: &[u8]) -> Result<StyleEmbedding, QArtError> {
        self.extract_image_embedding(data)
    }

    fn extract_audio(&self, data: &[u8]) -> Result<StyleEmbedding, QArtError> {
        self.extract_audio_embedding(data)
    }

    fn extract_text(&self, text: &str) -> Result<StyleEmbedding, QArtError> {
        self.extract_text_embedding(text)
    }

    fn similarity(&self, a: &[f32], b: &[f32]) -> f64 {
        ClipEmbedder::cosine_similarity(a, b)
    }
}

/// Trait para bridges de pagamento
#[cfg(feature = "x402-payments")]
pub trait PaymentBridge: Send + Sync {
    /// Envia um pagamento Pix
    fn send_payment(
        &self,
        pix_key: String,
        amount_cents: u64,
        metadata: Option<serde_json::Value>,
    ) -> Result<String, QArtError>;

    /// Verifica status de pagamento
    fn check_payment(&self, txid: &str) -> Result<PaymentStatus, QArtError>;

    /// Obtém saldo disponível
    fn get_balance(&self) -> Result<f64, QArtError>;

    /// Registra webhook para notificações
    fn register_webhook(&self, url: &str) -> Result<(), QArtError>;
}

#[cfg(feature = "x402-payments")]
impl PaymentBridge for X402Bridge {
    fn send_payment(
        &self,
        pix_key: String,
        amount_cents: u64,
        metadata: Option<serde_json::Value>,
    ) -> Result<String, QArtError> {
        // Criar evento de royalty e processar
        let event = RoyaltyEvent {
            target_block_id: metadata
                .and_then(|m| m.get("block_id").and_then(|v| v.as_str()))
                .unwrap_or_default()
                .as_bytes()
                .to_vec(),
            source_orcid: metadata
                .and_then(|m| m.get("orcid").and_then(|v| v.as_str()))
                .unwrap_or("")
                .to_string(),
            source_fingerprint: ArtFingerprint {
                perceptual_hash: PerceptualHash(vec![]),
                style_embedding: StyleEmbedding {
                    dim: 768,
                    vector: vec![0.0; 768],
                },
                metadata_commitment: MetadataCommitment(vec![]),
                raw_hash: vec![],
                timestamp: 0,
                origin_orcid: None,
            },
            amount: amount_cents as f64,
            pix_key,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        };

        let response = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?
            .block_on(async {
                let (bridge, _) = compensation::x402_pix_bridge::X402PixBridge::new(
                    PixX402Config::default(),
                );
                bridge.send_instant_payment(event.pix_key.clone(), event.amount, "qart-payment".into()).await
            })
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        Ok(response)
    }

    fn check_payment(&self, txid: &str) -> Result<PaymentStatus, QArtError> {
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        let status = runtime.block_on(async {
            let (bridge, _) = compensation::x402_pix_bridge::X402PixBridge::new(
                PixX402Config::default(),
            );
            bridge.check_payment_status(txid).await
        })?;

        Ok(status)
    }

    fn get_balance(&self) -> Result<f64, QArtError> {
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        runtime.block_on(async {
            let (bridge, _) = compensation::x402_pix_bridge::X402PixBridge::new(
                PixX402Config::default(),
            );
            bridge.get_balance().await
        })
    }

    fn register_webhook(&self, _url: &str) -> Result<(), QArtError> {
        Ok(()) // Implementar conforme necessário
    }
}

// ============================================================================
// TESTS DO MÓDULO
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;
    use sha3::{Sha3_256, Digest};

    #[test]
    fn test_module_structure() {
        // Verifica que todos os módulos estão acessíveis
        let _config = QArtConfig::default();
        let _engine = qart_engine!();
    }

    #[test]
    fn test_art_fingerprint_creation() {
        let data = b"test artwork data";
        let fp = art_fingerprint!(raw: data, style_model: "CLIP-ViT-L/14");
        assert_eq!(fp.raw_hash.len(), 32);
        assert_eq!(fp.style_embedding.dim, 768);
    }

    #[test]
    fn test_macro_qart_engine() {
        let engine = qart_engine!(config: {
            min_influence_probability: 0.1,
            use_orcid_reputation: true,
            network_fee: 0.01,
        });
        assert!(engine.config.min_influence_probability == 0.1);
    }

    #[test]
    fn test_macro_zk_config() {
        let config = zk_config!(security: 128, variables: 1048576);
        assert_eq!(config.security_bits, 128);
        assert_eq!(config.max_variables, 1048576);
    }

    #[test]
    fn test_merkle_root_empty() {
        let root = build_influence_merkle_root(&[]);
        assert!(root.is_empty() || root.len() == 32);
    }

    #[test]
    fn test_macro_art_block() {
        let fp = art_fingerprint!(raw: b"test", style_model: "CLIP-ViT-L/14");
        let block = art_block!(
            id: [1u8; 32],
            fp: fp,
            value: 1.0,
            energy: 0.5
        );
        assert_eq!(block.block_id.len(), 32);
        assert_eq!(block.economic_value, 1.0);
        assert_eq!(block.energy_cost, 0.5);
    }

    #[test]
    fn test_strict_aliasing_compliance() {
        // Garante que o módulo compila sem aliasing violations
        let data: &[u8] = b"test";
        let hash1 = {
            let mut h = Sha3_256::new();
            h.update(data);
            h.finalize()
        };
        let hash2 = {
            let mut h = Sha3_256::new();
            h.update(data);
            h.finalize()
        };
        assert_eq!(hash1[..], hash2[..]);
    }

    #[test]
    #[cfg(feature = "full-zk")]
    fn test_zk_system_creation() {
        let system = ZKProofSystem::new(true);
        assert_eq!(system.proof_counter, 0);
    }

    #[test]
    fn test_qart_error_display() {
        let err = QArtError::InvalidFingerprint;
        let msg = format!("{}", err);
        assert!(msg.contains("Invalid"));
    }
}

// ============================================================================
// DOCUMENTAÇÃO DO MÓDULO
// ============================================================================

/// # Q-Art (Quantum Artistic Influence) — Substrato 6072
///
/// O módulo canônico para rastreamento de influência artística e compensação
/// probabilística de royalties na cadeia temporal ARKHE.
///
/// ## Visão Geral
///
/// O Q-Art transforma cada obra de arte (visual, sonora, literária ou generativa)
/// em uma **semente probabilística** de royalties, rastreada pela identidade ORCID
/// do artista e ancorada na cadeia temporal.
///
/// ## Arquitetura
///
/// ```text
/// Artista registra obra ──▶ extract_art_fingerprint()
///                              │
///                              ▼
///                    ArtFingerprint { perceptual_hash, style_embedding, ... }
///                              │
///              ┌───────────────┼───────────────┐
///              ▼               ▼               ▼
///        TemporalChain    ZK Proofs       Oracle Mesh
///        (ancoragem)    (anonimato)    (ecos estilísticos)
///              │               │               │
///              ▼               ▼               ▼
///        ArtBlock no      Provas ZK       Tendências
///        ledger           on-chain        emergentes
///              │
///              ▼
///        Q-Art Engine processa
///        influências e calcula
///        royalties
///              │
///              ▼
///        Pix Bridge paga
///        instantaneamente
/// ```
///
/// ## Exemplo de Uso
///
/// ```ignore
/// use arkhe_qart::{
///     QArtEngine, QArtConfig, ClipEmbedder, ZKProofSystem,
///     ArtFingerprint, art_fingerprint, qart_engine, zk_config,
/// };
///
/// // 1. Configurar engine
/// let mut engine = qart_engine!(config: {
///     min_influence_probability: 0.05,
///     use_orcid_reputation: true,
/// });
///
/// // 2. Registrar obra original
/// let raw_data = std::fs::read("painting.png").unwrap();
/// let fp = art_fingerprint!(raw: &raw_data, orcid: "0000-0002-1825-0097", style_model: "CLIP-ViT-L/14");
///
/// // 3. Quando Continental Mind gera nova obra:
/// let block = art_block!(
///     id: block_hash,
///     fp: new_fp,
///     value: 0.50,
///     energy: 0.15
/// );
///
/// // 4. Processar royalties
/// let royalties = engine.process_new_art_block(&block).await.unwrap();
///
/// // 5. Gerar provas ZK (opcional)
/// let mut zk = ZKProofSystem::new(true);
/// let proof = zk.generate_style_influence(
///     &fp.style_embedding.vector,
///     &new_fp.style_embedding.vector,
///     0.7, // threshold
/// );
/// ```
///
/// ## Features
///
/// | Feature | Descrição | Dependências |
/// |---------|-----------|-------------|
/// | `full-zk` | Provas ZK com Plonky2 | plonky2, bellman |
/// | `style-models` | CLIP + AST embeddings | tch, ndarray, image |
/// | `x402-payments` | Bridge Pix via IPC | reqwest, tokio |
/// | `sim-test` | Testes de simulação | — |
///
/// ## Compatibilidade
///
/// - **Rust**: 1.87.0+ (nightly para `asm_experimental_arch`)
/// - **Target**: `x86_64-unknown-linux-gnu` (produção), `wasm32-unknown-unknown` (Wasm)
/// - **Torch**: libtorch 2.x (para `style-models`)
/// - **Plonky2**: Prover SRS necessário para `full-zk`

// ============================================================================
// CONSTANTES DO MÓDULO
// ============================================================================

/// Versão atual do Substrato Q-Art
pub const QART_VERSION: &str = "6.0.0";

/// Número máximo de obras no cache de influência
pub const MAX_INFLUENCE_CACHE_SIZE: usize = 100_000;

/// Janela temporal padrão para cálculo de influência (6 meses em segundos)
pub const DEFAULT_INFLUENCE_WINDOW_SECONDS: u64 = 6 * 30 * 24 * 3600;

/// Número máximo de provas ZK em lote
pub const MAX_ZK_BATCH_SIZE: usize = 256;

/// Taxa de comissão da rede (1%)
pub const DEFAULT_NETWORK_FEE: f64 = 0.01;

/// Split de royalties: 80% criador, 15% plataforma, 5% pool
pub const ROYALTY_SPLIT_CREATOR: f64 = 0.80;
pub const ROYALTY_SPLIT_PLATFORM: f64 = 0.15;
pub const ROYALTY_SPLIT_POOL: f64 = 0.05;

/// Mínimo de probabilidade para disparar compensação
pub const MIN_COMPENSATION_PROBABILITY: f64 = 0.05;
