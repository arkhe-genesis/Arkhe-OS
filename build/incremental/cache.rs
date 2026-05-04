// build/incremental/cache.rs — Cache incremental com hash dependente de features
use anyhow::{Result, Context};
use sha2::{Sha256, Digest};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};

/// Entry no cache de compilação incremental
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheEntry {
    /// Hash do conteúdo fonte + features + toolchain
    pub cache_key: String,

    /// Hash do artefato compilado resultante
    pub artifact_hash: String,

    /// Timestamp de criação
    pub created_at: u64,

    /// Features habilitadas para este build
    pub features: Vec<String>,

    /// Toolchain version usada
    pub toolchain: String,

    /// Caminho para o artefato no cache
    pub artifact_path: PathBuf,
}

/// Gerenciador de cache incremental
pub struct IncrementalCache {
    /// Diretório raiz do cache
    cache_dir: PathBuf,

    /// Índice de entries (em memória)
    index: HashMap<String, CacheEntry>,

    /// Limite de idade do cache em dias
    max_age_days: u64,
}

impl IncrementalCache {
    /// Criar novo cache incremental
    pub fn new(cache_dir: PathBuf, max_age_days: u64) -> Result<Self> {
        fs::create_dir_all(&cache_dir)?;

        // Carregar índice existente
        let index_path = cache_dir.join("index.json");
        let index = if index_path.exists() {
            let content = fs::read_to_string(&index_path)?;
            serde_json::from_str(&content).unwrap_or_default()
        } else {
            HashMap::new()
        };

        Ok(Self {
            cache_dir,
            index,
            max_age_days,
        })
    }

    /// Calcular cache key para um módulo com features específicas
    pub fn compute_cache_key(
        source_path: &Path,
        features: &[String],
        toolchain_version: &str,
    ) -> Result<String> {
        let mut hasher = Sha256::new();

        // Hash do conteúdo fonte
        let source = fs::read(source_path)
            .context(format!("Failed to read source: {:?}", source_path))?;
        hasher.update(&source);

        // Hash das features (ordenadas para determinismo)
        let mut sorted_features = features.to_vec();
        sorted_features.sort();
        hasher.update(sorted_features.join(",").as_bytes());

        // Hash do toolchain
        hasher.update(toolchain_version.as_bytes());

        Ok(format!("{:x}", hasher.finalize()))
    }

    /// Tentar obter artefato do cache
    pub fn get_artifact(&self, cache_key: &str) -> Option<PathBuf> {
        self.index.get(cache_key).and_then(|entry| {
            // Verificar se artefato ainda existe
            if entry.artifact_path.exists() {
                Some(entry.artifact_path.clone())
            } else {
                None
            }
        })
    }

    /// Armazenar novo artefato no cache
    pub fn put_artifact(
        &mut self,
        cache_key: String,
        artifact_path: PathBuf,
        features: Vec<String>,
        toolchain: String,
    ) -> Result<()> {
        // Calcular hash do artefato
        let artifact_hash = Self::hash_file(&artifact_path)?;

        // Copiar artefato para diretório do cache (content-addressable)
        let cached_path = self.cache_dir.join(&cache_key);
        fs::copy(&artifact_path, &cached_path)?;

        // Criar entry
        let entry = CacheEntry {
            cache_key: cache_key.clone(),
            artifact_hash,
            created_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)?
                .as_secs(),
            features,
            toolchain,
            artifact_path: cached_path,
        };

        // Atualizar índice
        self.index.insert(cache_key, entry);
        self.save_index()?;

        Ok(())
    }

    /// Limpar entries expirados do cache
    pub fn cleanup(&mut self) -> Result<usize> {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)?
            .as_secs();

        let max_age_secs = self.max_age_days * 24 * 60 * 60;
        let mut removed = 0;

        // Coletar keys para remover
        let to_remove: Vec<String> = self.index.iter()
            .filter(|(_, entry)| now - entry.created_at > max_age_secs)
            .map(|(key, _)| key.clone())
            .collect();

        // Remover entries e artefatos
        for key in to_remove {
            if let Some(entry) = self.index.remove(&key) {
                let _ = fs::remove_file(&entry.artifact_path);
                removed += 1;
            }
        }

        // Salvar índice atualizado
        if removed > 0 {
            self.save_index()?;
        }

        Ok(removed)
    }

    /// Salvar índice no disco
    fn save_index(&self) -> Result<()> {
        let index_path = self.cache_dir.join("index.json");
        let content = serde_json::to_string_pretty(&self.index)?;
        fs::write(index_path, content)?;
        Ok(())
    }

    /// Calcular hash SHA-256 de arquivo
    fn hash_file(path: &Path) -> Result<String> {
        let mut hasher = Sha256::new();
        let mut file = fs::File::open(path)?;
        std::io::copy(&mut file, &mut hasher)?;
        Ok(format!("{:x}", hasher.finalize()))
    }

    /// Obter estatísticas do cache
    pub fn get_stats(&self) -> CacheStats {
        let total_entries = self.index.len();
        let total_size: u64 = self.index.values()
            .filter_map(|e| fs::metadata(&e.artifact_path).ok())
            .map(|m| m.len())
            .sum();

        CacheStats {
            total_entries,
            total_size_bytes: total_size,
            total_size_mb: total_size as f64 / (1024.0 * 1024.0),
            max_age_days: self.max_age_days,
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct CacheStats {
    pub total_entries: usize,
    pub total_size_bytes: u64,
    pub total_size_mb: f64,
    pub max_age_days: u64,
}
