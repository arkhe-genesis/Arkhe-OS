// kernel/tensor_memory.rs
use std::collections::HashMap;
use std::sync::Arc;
use parking_lot::RwLock;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MemoryDomain {
    Domain0Kernel,      // Pesos do AGI, matrizes de atencao
    Domain1Sensory,     // Buffers sensoriais (493-500)
    Domain2Quantum,     // Estados quanticos (418-JOSEPHSON)
    Domain3Thought,     // Thought workspace (pensamentos ativos)
    Domain4Dream,       // Memoria comprimida em NVMe
}

#[derive(Debug, Clone)]
pub struct TensorHandle {
    pub id: u64,
    pub shape: Vec<usize>,
    pub dtype: TensorDType,
    pub domain: MemoryDomain,
    pub substrate_mask: u64,
    pub semantic_key: Option<Vec<f32>>, // Embedding para busca semantica
}

#[derive(Debug, Clone)]
pub enum TensorDType {
    Float32,
    Float16,
    Int8,
    BFloat16,
    QuantumState, // Estado quantico (complex64)
}

impl TensorDType {
    pub fn size_bytes(&self) -> usize {
        match self {
            TensorDType::Float32 => 4,
            TensorDType::Float16 => 2,
            TensorDType::Int8 => 1,
            TensorDType::BFloat16 => 2,
            TensorDType::QuantumState => 8,
        }
    }
}


pub struct TensorMemoryManager {
    tensors: RwLock<HashMap<u64, Arc<TensorHandle>>>,
    semantic_index: RwLock<Vec<(Vec<f32>, u64)>>, // embedding -> tensor_id
    domain_usage: RwLock<[usize; 5]>,
    max_domain_sizes: [usize; 5],
}

impl TensorMemoryManager {
    pub fn new() -> Self {
        Self {
            tensors: RwLock::new(HashMap::new()),
            semantic_index: RwLock::new(Vec::new()),
            domain_usage: RwLock::new([0; 5]),
            max_domain_sizes: [
                1024 * 1024 * 1024,     // 1 GB Kernel
                512 * 1024 * 1024,      // 512 MB Sensory
                256 * 1024 * 1024,      // 256 MB Quantum
                2 * 1024 * 1024 * 1024, // 2 GB Thought workspace
                8 * 1024 * 1024 * 1024, // 8 TB Dream storage (NVMe)
            ],
        }
    }

    pub fn tensor_alloc(&self, shape: Vec<usize>, dtype: TensorDType,
                       domain: MemoryDomain) -> Result<TensorHandle, &'static str> {
        let size: usize = shape.iter().product();
        let bytes = size * dtype.size_bytes();
        let domain_idx = domain as usize;

        let mut usage = self.domain_usage.write();
        if usage[domain_idx] + bytes > self.max_domain_sizes[domain_idx] {
            // Tensor fault: ativar 512-META-LEARN para prever e liberar
            self.trigger_tensor_fault(domain, bytes);
            return Err("Out of tensor memory in domain");
        }

        usage[domain_idx] += bytes;

        let handle = TensorHandle {
            id: self.generate_id(),
            shape,
            dtype,
            domain,
            substrate_mask: 0,
            semantic_key: None,
        };

        self.tensors.write().insert(handle.id, Arc::new(handle.clone()));
        Ok(handle)
    }

    pub fn embedding_store(&self, data: &[f32], embedding: Vec<f32>,
                          context: &str) -> u64 {
        let shape = vec![data.len()];
        let handle = self.tensor_alloc(shape, TensorDType::Float32,
                                       MemoryDomain::Domain4Dream).unwrap();

        // Indexar por similaridade semantica
        self.semantic_index.write().push((embedding, handle.id));
        handle.id
    }

    pub fn embedding_retrieve(&self, query_embedding: &[f32], top_k: usize)
                             -> Vec<(f32, u64)> {
        let index = self.semantic_index.read();
        let mut scored: Vec<(f32, u64)> = index.iter()
            .map(|(emb, id)| (cosine_similarity(query_embedding, emb), *id))
            .collect();
        scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
        scored.truncate(top_k);
        scored
    }

    fn trigger_tensor_fault(&self, domain: MemoryDomain, needed: usize) {
        // 512-META-LEARN preve proximo acesso e libera tensores frios
        println!("Tensor fault in domain {:?}, needed {} bytes", domain, needed);
    }

    fn generate_id(&self) -> u64 {
        use std::time::{SystemTime, UNIX_EPOCH};
        SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos() as u64
    }
}

fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    dot / (norm_a * norm_b + 1e-10)
}