use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use half::f16;
use std::path::PathBuf;
use serde::{Serialize, Deserialize};

/// Chave de acesso ao gradient store
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct GradientKey {
    pub shard_id: u32,
    pub step: u64,
    pub layer_idx: u32,
}

/// Entrada no gradient store
#[derive(Clone, Debug)]
pub struct GradientEntry {
    pub key: GradientKey,
    pub gradients: Vec<f32>, // Flattened
    pub timestamp: u64,
    pub is_compressed: bool,
    pub metadata: GradientMetadata,
}

/// Metadados do gradiente
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GradientMetadata {
    pub layer_name: String,
    pub activation_shape: Vec<usize>,
    pub gradient_norm: f32,
    pub learning_rate: f32,
}

/// Armazenamento de gradientes com múltiplos níveis
pub struct GradientStore {
    hot_cache: HashMap<GradientKey, GradientEntry>,
    max_hot_entries: usize,
    storage_dir: PathBuf,
    compression_enabled: bool,
}

impl GradientStore {
    pub fn new(max_shards: usize) -> Self {
        Self {
            hot_cache: HashMap::with_capacity(max_shards * 10),
            max_hot_entries: max_shards * 50,
            storage_dir: std::env::temp_dir().join("arkhe_gradients"),
            compression_enabled: true,
        }
    }
}
