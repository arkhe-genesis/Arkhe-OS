// ============================================================================
// ORCID Registry — Mapeamento ORCID ↔ DataFingerprint
// ============================================================================
//
// Mantém o vínculo entre a identidade ORCID do pesquisador e os
// fingerprints dos dados que ele contribuiu. Cada vínculo é ancorado
// na TemporalHashChain como uma transação imutável.
// ============================================================================

use std::collections::{HashMap, HashSet};
use std::sync::{Arc, RwLock};
use serde::{Serialize, Deserialize};
use tracing::{info, warn};

use crate::auth::{OrcidRecord, OrcidAuthError};
use crate::proof::ZkProofParams;

/// Tipo de contribuição do pesquisador
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ContributionType {
    /// Dataset fornecido diretamente
    Dataset,
    /// Artigo/paper indexado
    Publication,
    /// Código-fonte contribuído
    Codebase,
    /// Anotação ou rotulação de dados
    Annotation,
    /// Modelo treinado com dados do contribuidor
    ModelWeights,
    /// Feedback ou avaliação
    Feedback,
}

/// Vínculo entre ORCID e DataFingerprint
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OrcidDataLink {
    pub orcid_id: String,
    pub fingerprint: Vec<u8>,       // SHA3-256 do conteúdo
    pub contribution_type: ContributionType,
    pub timestamp: u64,              // Unix timestamp
    pub signature: Vec<u8>,          // Assinatura ORCID sobre fingerprint
    pub metadata: ContributionMetadata,
}

/// Metadados da contribuição
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ContributionMetadata {
    pub dataset_name: Option<String>,
    pub doi: Option<String>,
    pub license: Option<String>,
    pub description: Option<String>,
    pub tags: Vec<String>,
    pub size_bytes: Option<u64>,
    pub hash_algorithm: String, // "sha3-256", "blake3"
}

/// Registro de mapeamento ORCID ↔ Fingerprints
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OrcidRegistry {
    // ORCID ID → Lista de fingerprints associados
    orcid_to_fingerprints: HashMap<String, HashSet<Vec<u8>>>,
    // Fingerprint → Lista de ORCIDs que contribuíram
    fingerprint_to_orcids: HashMap<Vec<u8>, HashSet<String>>,
    // Links completos para auditoria
    links: Vec<OrcidDataLink>,
    // Máximo de fingerprints por ORCID (proteção contra abuso)
    max_fingerprints_per_orcid: usize,
}

/// Erro do registro ORCID
#[derive(Debug)]
pub enum RegistryError {
    NotAuthenticated(String),

    DuplicateFingerprint,

    LimitReached(usize),

    InvalidSignature,

    StorageError(String),

    ProfileNotFound,
}

impl OrcidRegistry {
    /// Criar novo registro vazio
    pub fn new(max_fingerprints_per_orcid: usize) -> Self {
        Self {
            orcid_to_fingerprints: HashMap::new(),
            fingerprint_to_orcids: HashMap::new(),
            links: Vec::new(),
            max_fingerprints_per_orcid,
        }
    }

    /// Registrar contribuição de um pesquisador
    pub fn register_contribution(
        &mut self,
        orcid_record: &OrcidRecord,
        fingerprint: &[u8],
        contribution_type: ContributionType,
        signature: &[u8],
        metadata: ContributionMetadata,
    ) -> Result<OrcidDataLink, RegistryError> {
        // Verificar limite
        let current_count = self.orcid_to_fingerprints
            .get(&orcid_record.orcid_id)
            .map(|s| s.len())
            .unwrap_or(0);

        if current_count >= self.max_fingerprints_per_orcid {
            return Err(RegistryError::LimitReached(self.max_fingerprints_per_orcid));
        }

        // Verificar duplicata
        let fp_bytes = fingerprint.to_vec();
        if let Some(fps) = self.orcid_to_fingerprints.get(&orcid_record.orcid_id) {
            if fps.contains(&fp_bytes) {
                return Err(RegistryError::DuplicateFingerprint);
            }
        }

        // TODO: Verificar assinatura com chave pública ORCID
        // verify_signature(orcid_record, fingerprint, signature)?;

        // Criar link
        let link = OrcidDataLink {
            orcid_id: orcid_record.orcid_id.clone(),
            fingerprint: fp_bytes.clone(),
            contribution_type,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0),
            signature: signature.to_vec(),
            metadata,
        };

        // Atualizar índices
        self.orcid_to_fingerprints
            .entry(orcid_record.orcid_id.clone())
            .or_default()
            .insert(fp_bytes.clone());

        self.fingerprint_to_orcids
            .entry(fp_bytes)
            .or_default()
            .insert(orcid_record.orcid_id.clone());

        self.links.push(link.clone());

        info!(
            orcid_id = %orcid_record.orcid_id,
            fingerprint = %hex::encode(&fingerprint[..8]),
            "Contribution registered"
        );

        Ok(link)
    }

    /// Obter todos os ORCIDs associados a um fingerprint
    pub fn get_contributors(&self, fingerprint: &[u8]) -> Vec<&String> {
        self.fingerprint_to_orcids
            .get(fingerprint)
            .map(|s| s.iter().collect())
            .unwrap_or_default()
    }

    /// Obter todos os fingerprints associados a um ORCID
    pub fn get_fingerprints(&self, orcid_id: &str) -> Option<&HashSet<Vec<u8>>> {
        self.orcid_to_fingerprints.get(orcid_id)
    }

    /// Obter todos os links de contribuição
    pub fn get_all_links(&self) -> &[OrcidDataLink] {
        &self.links
    }

    /// Verificar se um ORCID contribuiu com um dado específico
    pub fn has_contributed(&self, orcid_id: &str, fingerprint: &[u8]) -> bool {
        self.orcid_to_fingerprints
            .get(orcid_id)
            .map(|fps| fps.contains(fingerprint))
            .unwrap_or(false)
    }

    /// Buscar links por intervalo de tempo
    pub fn find_links_in_time_range(
        &self,
        orcid_id: &str,
        start: u64,
        end: u64,
    ) -> Vec<&OrcidDataLink> {
        self.links
            .iter()
            .filter(|link| {
                link.orcid_id == orcid_id &&
                link.timestamp >= start &&
                link.timestamp <= end
            })
            .collect()
    }

    /// Verificar se ORCID está registrado no sistema
    pub fn is_registered(&self, orcid_id: &str) -> bool {
        self.orcid_to_fingerprints.contains_key(orcid_id)
    }

    /// Número total de contribuidores
    pub fn contributor_count(&self) -> usize {
        self.orcid_to_fingerprints.len()
    }

    /// Número total de fingerprints registrados
    pub fn fingerprint_count(&self) -> usize {
        self.fingerprint_to_orcids.len()
    }

    /// Persistir registro em disco
    pub fn save_to_file(&self, path: &std::path::Path) -> Result<(), RegistryError> {
        let json = serde_json::to_string_pretty(self)
            .map_err(|e| RegistryError::StorageError(e.to_string()))?;
        std::fs::write(path, json)
            .map_err(|e| RegistryError::StorageError(e.to_string()))?;
        Ok(())
    }

    /// Carregar registro de disco
    pub fn load_from_file(path: &std::path::Path) -> Result<Self, RegistryError> {
        let json = std::fs::read_to_string(path)
            .map_err(|e| RegistryError::StorageError(e.to_string()))?;
        serde_json::from_str(&json)
            .map_err(|e| RegistryError::StorageError(e.to_string()))
    }
}

// Thread-safe wrapper para uso concorrente
#[derive(Clone, Debug)]
pub struct SharedOrcidRegistry {
    inner: Arc<RwLock<OrcidRegistry>>,
}

impl SharedOrcidRegistry {
    pub fn new(max_fingerprints: usize) -> Self {
        Self {
            inner: Arc::new(RwLock::new(OrcidRegistry::new(max_fingerprints))),
        }
    }

    pub fn register(
        &self,
        record: &OrcidRecord,
        fingerprint: &[u8],
        ctype: ContributionType,
        signature: &[u8],
        metadata: ContributionMetadata,
    ) -> Result<OrcidDataLink, RegistryError> {
        self.inner.write().unwrap().register_contribution(
            record, fingerprint, ctype, signature, metadata,
        )
    }

    pub fn get_contributors(&self, fingerprint: &[u8]) -> Vec<String> {
        self.inner.read().unwrap()
            .get_contributors(fingerprint)
            .into_iter()
            .cloned()
            .collect()
    }
}

impl std::fmt::Display for RegistryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}
impl std::error::Error for RegistryError {}
