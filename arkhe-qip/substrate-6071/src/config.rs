// ============================================================================
// ARKHE QIP — Configuration
// ============================================================================

use std::time::Duration;

use serde::{Deserialize, Serialize};

/// Configuração global do sistema QIP
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct QipConfig {
    /// Configuração de cálculo de influência
    pub influence: InfluenceConfig,

    /// Configuração de compensação
    pub compensation: CompensationConfig,

    /// Configuração de proveniência
    pub provenance: ProvenanceConfig,

    /// Configuração do marketplace/oracle
    pub marketplace: MarketplaceConfig,

    /// Configuração de cache
    pub cache: CacheConfig,
}

impl Default for QipConfig {
    fn default() -> Self {
        Self {
            influence: InfluenceConfig::default(),
            compensation: CompensationConfig::default(),
            provenance: ProvenanceConfig::default(),
            marketplace: MarketplaceConfig::default(),
            cache: CacheConfig::default(),
        }
    }
}

/// Configuração de influência
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct InfluenceConfig {
    pub num_monte_carlo_samples: usize,
    pub similarity_threshold: f64,
    pub decay_factor: f64,
    pub min_probability: f64,
    pub max_shards_to_consider: usize,
    pub enable_shapley: bool,
    pub enable_tracin: bool,
    pub enable_gradient_similarity: bool,
    pub enable_ensemble: bool,
    /// Tempo máximo de cálculo por bloco (ms)
    pub max_computation_time_ms: u64,
}

impl Default for InfluenceConfig {
    fn default() -> Self {
        Self {
            num_monte_carlo_samples: 1000,
            similarity_threshold: 0.5,
            decay_factor: 0.99,
            min_probability: 0.01,
            max_shards_to_consider: 100,
            enable_shapley: true,
            enable_tracin: true,
            enable_gradient_similarity: true,
            enable_ensemble: true,
            max_computation_time_ms: 60_000, // 1 minuto por bloco
        }
    }
}

/// Configuração de compensação
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CompensationConfig {
    /// Valor mínimo para compensação (em ARKHE)
    pub min_reward_arkhe: f64,

    /// Taxa de conversão ARKHE → centavos BRL
    pub conversion_rate_brl: f64,

    /// Taxa de saque (%)
    pub cashout_fee_percent: f64,

    /// Mínimo para saque (centavos)
    pub min_cashout_cents: u64,

    /// Habilitar pagamentos automáticos
    pub auto_payments: bool,

    /// Intervalo entre pagamentos automáticos (horas)
    pub auto_payment_interval_hours: u64,

    /// Limite diário de pagamentos (centavos)
    pub daily_payment_limit_cents: u64,

    /// Habilitar ZK proofs de pagamento
    pub zk_payment_proofs: bool,
}

impl Default for CompensationConfig {
    fn default() -> Self {
        Self {
            min_reward_arkhe: 0.01,
            conversion_rate_brl: 0.05, // 1 ARKHE = 5 centavos
            cashout_fee_percent: 2.0,
            min_cashout_cents: 50,
            auto_payments: true,
            auto_payment_interval_hours: 24,
            daily_payment_limit_cents: 10_000_000, // R$100.000
            zk_payment_proofs: true,
        }
    }
}

/// Configuração de proveniência
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ProvenanceConfig {
    /// Algoritmo de commitment
    pub commitment_algorithm: CommitmentAlgorithm,

    /// Habilitar provas ZK completas
    pub enable_full_zk: bool,

    /// Profundidade máxima da Merkle tree
    pub merkle_tree_depth: usize,

    /// Intervalo de ancoragem na temporal chain (blocos)
    pub anchor_interval_blocks: u64,
}

impl Default for ProvenanceConfig {
    fn default() -> Self {
        Self {
            commitment_algorithm: CommitmentAlgorithm::Poseidon,
            enable_full_zk: true,
            merkle_tree_depth: 32,
            anchor_interval_blocks: 100,
        }
    }
}

/// Algoritmo de commitment
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum CommitmentAlgorithm {
    Pedersen,
    Poseidon,
    SHA3,
}

/// Configuração do marketplace
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MarketplaceConfig {
    /// Leilão de dados por entropia habilitado
    pub entropy_auction_enabled: bool,

    /// Preço base por unit de entropia
    pub base_entropy_price: f64,

    /// Leilão mínimo de itens
    pub min_auction_items: usize,

    /// Leilão máximo de itens
    pub max_auction_items: usize,

    /// Duração do leilão (blocos)
    pub auction_duration_blocks: u64,
}

impl Default for MarketplaceConfig {
    fn default() -> Self {
        Self {
            entropy_auction_enabled: true,
            base_entropy_price: 0.001,
            min_auction_items: 10,
            max_auction_items: 1000,
            auction_duration_blocks: 10_000,
        }
    }
}

/// Configuração de cache
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CacheConfig {
    /// TTL do cache de influência (segundos)
    pub influence_cache_ttl: u64,

    /// TTL do cache de reputação (segundos)
    pub reputation_cache_ttl: u64,

    /// Tamanho máximo do cache
    pub max_cache_size: usize,

    /// Habilitar cache de provas ZK
    pub zk_proof_cache: bool,
}

impl Default for CacheConfig {
    fn default() -> Self {
        Self {
            influence_cache_ttl: 3_600, // 1 hora
            reputation_cache_ttl: 604_800, // 7 dias
            max_cache_size: 100_000,
            zk_proof_cache: true,
        }
    }
}

/// Configuração de ORCID
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OrcidConfig {
    /// Client ID para OAuth2 com ORCID
    pub client_id: String,

    /// Client secret
    pub client_secret: String,

    /// Redirect URI
    pub redirect_uri: String,

    /// Ambiente (sandbox/production)
    pub sandbox: bool,

    /// Cache de ORCIDs verificados
    pub verified_orcid_cache: bool,
}
