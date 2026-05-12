// ============================================================================
// ARKHE QIP — Shared Types
// ============================================================================

use std::sync::Arc;
use serde::{Serialize, Deserialize};
use sha3::{Sha3_256, Digest};
use std::collections::HashMap;

/// Fingerprint único de um conjunto de dados
/// Gerado a partir do conteúdo + metadados
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct DataFingerprint {
    /// Hash do conteúdo dos dados
    pub content_hash: [u8; 32],
    /// Hash dos metadados
    pub metadata_hash: [u8; 32],
    /// Algoritmo de hash utilizado
    pub algorithm: HashAlgorithm,
    /// Timestamp de criação
    pub created_at: u64,
    /// Tamanho em bytes
    pub size_bytes: u64,
}

impl DataFingerprint {
    /// Criar fingerprint a partir de dados brutos
    pub fn from_data(data: &[u8], metadata: &[u8]) -> Self {
        let content_hash = Sha3_256::digest(data).into();
        let metadata_hash = Sha3_256::digest(metadata).into();

        Self {
            content_hash,
            metadata_hash,
            algorithm: HashAlgorithm::SHA3_256,
            created_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0),
            size_bytes: data.len() as u64,
        }
    }

    /// Criar a partir de BLAKE3 (mais rápido)
    pub fn from_data_blake3(data: &[u8], metadata: &[u8]) -> Self {
        let content_hash: [u8; 32] = *blake3::hash(data).as_bytes();
        let metadata_hash: [u8; 32] = *blake3::hash(metadata).as_bytes();

        Self {
            content_hash,
            metadata_hash,
            algorithm: HashAlgorithm::BLAKE3,
            created_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0),
            size_bytes: data.len() as u64,
        }
    }

    /// Converter para bytes
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::new();
        bytes.extend_from_slice(&self.content_hash);
        bytes.extend_from_slice(&self.metadata_hash);
        bytes.push(self.algorithm as u8);
        bytes.extend_from_slice(&self.created_at.to_le_bytes());
        bytes.extend_from_slice(&self.size_bytes.to_le_bytes());
        bytes
    }

    /// Hash combinado (para tabelas hash)
    pub fn combined_hash(&self) -> [u8; 32] {
        let mut hasher = Sha3_256::new();
        hasher.update(&self.content_hash);
        hasher.update(&self.metadata_hash);
        hasher.finalize().into()
    }
}

impl std::fmt::Display for DataFingerprint {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "FP-{}", hex::encode(&self.content_hash[..8]))
    }
}

/// Algoritmo de hash
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum HashAlgorithm {
    SHA3_256 = 0,
    BLAKE3 = 1,
    SHA256 = 2,
}

/// Bloco temporal com metadados de inferência
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TemporalBlock {
    pub block_number: u64,
    pub block_hash: [u8; 32],
    pub previous_hash: [u8; 32],
    pub merkle_root: [u8; 32],
    pub timestamp: u64,
    pub delta_time_ms: u64,
    pub active_shards: Vec<u32>,
    pub token_count: u32,
    pub model_snapshot_hash: [u8; 32],
    pub energy_consumed_joules: f64,
}

impl TemporalBlock {
    /// Obter lista de shards ativos
    pub fn active_shards(&self) -> &[u32] {
        &self.active_shards
    }

    /// Obter idade do bloco (em segundos desde criação)
    pub fn age_seconds(&self) -> u64 {
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs().saturating_sub(self.timestamp))
            .unwrap_or(0)
    }
}

/// Snapshot do modelo em um momento específico
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ModelSnapshot {
    pub model_id: String,
    pub version: u64,
    pub total_params: u64,
    pub shard_snapshots: HashMap<u32, ShardSnapshot>,
    pub snapshot_hash: [u8; 32],
    pub captured_at: u64,
}

impl ModelSnapshot {
    /// Obter snapshot de um shard específico
    pub fn get_shard(&self, shard_id: u32) -> Option<&ShardSnapshot> {
        self.shard_snapshots.get(&shard_id)
    }
}

/// Snapshot de um shard individual
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ShardSnapshot {
    pub shard_id: u32,
    /// Gradientes/ativações armazenados
    pub gradient_memory: Vec<f32>,
    /// Pesos do shard
    pub weights_hash: [u8; 32],
    /// Último timestamp de atualização
    pub updated_at: u64,
    /// Número de inferências processadas
    pub inference_count: u64,
}

/// Resultado do cálculo de influência
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct InfluenceResult {
    /// Fingerprint dos dados analisados
    pub fingerprint: DataFingerprint,
    /// Bloco temporal analisado
    pub block_number: u64,
    /// Probabilidade de influência (0.0 - 1.0)
    pub probability: f64,
    /// Método utilizado para cálculo
    pub method: InfluenceMethod,
    /// Confiança do cálculo (0.0 - 1.0)
    pub confidence: f64,
    /// Detalhes adicionais
    pub details: InfluenceDetails,
}

/// Método de cálculo de influência
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum InfluenceMethod {
    ShapleyValue,
    TracIn,
    MonteCarlo,
    GradientSimilarity,
    Ensemble,
}

/// Detalhes do cálculo de influência
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct InfluenceDetails {
    /// Valores de Shapley (se aplicável)
    pub shapley_values: Option<HashMap<String, f64>>,
    /// Top-K shards mais influenciados
    pub top_k_shards: Vec<(u32, f64)>,
    /// Similaridade de gradientes
    pub gradient_similarity: Option<f64>,
    /// Número de samples utilizados
    pub num_samples: usize,
    /// Tempo de cálculo em ms
    pub computation_time_ms: u64,
    /// Método que gerou cada resultado
    pub sub_method_results: Vec<(InfluenceMethod, f64)>,
}

/// Evento de compensação
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CompensationEvent {
    /// Identificador do evento
    pub event_id: String,
    /// ORCID do pesquisador beneficiado
    pub orcid_id: String,
    /// Fingerprint dos dados que influenciaram
    pub fingerprint: DataFingerprint,
    /// Bloco temporal que contém o output
    pub block_number: u64,
    /// Probabilidade de influência
    pub probability: f64,
    /// Peso de reputação
    pub reputation_weight: f64,
    /// Valor bruto da recompensa (em ARKHE)
    pub raw_reward_arkhe: f64,
    /// Valor final da recompensa (em centavos BRL)
    pub final_reward_cents: u64,
    /// Endereço Pix para pagamento
    pub pix_key: String,
    /// Status do pagamento
    pub payment_status: PaymentStatus,
    /// Timestamp do evento
    pub timestamp: u64,
    /// Prova ZK (opcional)
    pub zk_proof: Option<Vec<u8>>,
}

/// Status de pagamento
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum PaymentStatus {
    Pending,
    Processing,
    Completed,
    Failed,
    Refunded,
}

/// Informações de um bloco para cálculo de valor econômico
#[derive(Clone, Debug)]
pub struct BlockValueInfo {
    /// Energia consumida em joules
    pub energy_joules: f64,
    /// Custo da energia em USD
    pub energy_cost_usd: f64,
    /// Número de tokens gerados
    pub token_count: u32,
    /// Valor médio por token (USD)
    pub token_value_usd: f64,
    /// Número de requisições atendidas
    pub request_count: u32,
    /// SLA contratual
    pub sla_tier: SLATier,
}

/// Tier de SLA
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum SLATier {
    Free,
    Basic,
    Professional,
    Enterprise,
    Research,
}

/// Grafo de dependência de dados
#[derive(Clone, Debug, Default)]
pub struct DataDependencyGraph {
    /// Nós: fingerprints de dados
    pub nodes: Vec<DataFingerprint>,
    /// Arestas: (source_idx, target_idx, weight)
    pub edges: Vec<(usize, usize, f64)>,
    /// Pesos de cada nó (importância relativa)
    pub node_weights: Vec<f64>,
}

/// Configuração de cálculo de influência
#[derive(Clone, Debug)]
pub struct InfluenceConfig {
    /// Número de amostras Monte Carlo
    pub num_monte_carlo_samples: usize,
    /// Threshold de similaridade para considerar influência
    pub similarity_threshold: f64,
    /// Fator de decaimento temporal
    pub decay_factor: f64,
    /// Mínimo probabilidade para compensação
    pub min_probability: f64,
    /// Máximo shards a considerar por bloco
    pub max_shards_to_consider: usize,
    /// Habilitar Shapley values
    pub enable_shapley: bool,
    /// Habilitar TracIn
    pub enable_tracin: bool,
    /// Habilitar similaridade de gradientes
    pub enable_gradient_similarity: bool,
    /// Habilitar ensemble (combinação de métodos)
    pub enable_ensemble: bool,
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
        }
    }
}
