use std::collections::{HashMap, HashSet};
use sha3::{Sha3_256, Digest};
use blake3;
use serde::{Serialize, Deserialize};

/// Nó do Merkle DAG
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MerkleNode {
    pub hash: [u8; 32],
    pub data: Option<Vec<u8>>, // None para nós intermediários
    pub parents: Vec<[u8; 32]>,
    pub depth: u32,
    pub timestamp: u64,
}

/// Merkle DAG para rastreamento de proveniência
pub struct MerkleDAG {
    nodes: HashMap<[u8; 32], MerkleNode>,
    roots: Vec<[u8; 32]>,
    max_depth: usize,
    node_count: u64,
}

impl MerkleDAG {
    pub fn new(max_depth: usize) -> Self {
        Self {
            nodes: HashMap::new(),
            roots: Vec::new(),
            max_depth,
            node_count: 0,
        }
    }

    pub fn add_leaf(&mut self, data: &[u8]) -> [u8; 32] {
        let hash = Self::hash_data(data);

        if self.nodes.contains_key(&hash) {
            return hash;
        }

        let node = MerkleNode {
            hash,
            data: Some(data.to_vec()),
            parents: Vec::new(),
            depth: 0,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0),
        };

        self.nodes.insert(hash, node);
        self.roots.push(hash);
        self.node_count += 1;

        hash
    }

    fn hash_data(data: &[u8]) -> [u8; 32] {
        let mut hasher = Sha3_256::new();
        hasher.update(data);
        hasher.finalize().into()
    }
}
