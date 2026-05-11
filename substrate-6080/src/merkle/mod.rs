pub struct MerkleTree<H> {
    _marker: std::marker::PhantomData<H>,
    root: Vec<u8>,
    leaves: Vec<Vec<u8>>,
}

pub struct MerkleProof {
    // some fields
}

#[derive(Debug)]
pub struct MerkleError;

#[derive(Default)]
pub struct TreeConfig;

pub struct LeafIndex(pub usize);

impl<H> MerkleTree<H> {
    pub fn new(leaves: &[Vec<u8>], _config: &TreeConfig) -> Result<Self, MerkleError> {
        let root = if leaves.is_empty() {
            vec![0; 32]
        } else {
            // Dummy root for testing
            vec![0; 32]
        };
        Ok(MerkleTree {
            _marker: std::marker::PhantomData,
            root,
            leaves: leaves.to_vec(),
        })
    }

    pub fn root(&self) -> Vec<u8> {
        self.root.clone()
    }

    pub fn proof(&self, _index: LeafIndex) -> Result<MerkleProof, MerkleError> {
        Ok(MerkleProof {})
    }
}

impl MerkleProof {
    pub fn verify(&self, _root: &[u8], _leaf: &[u8]) -> Result<bool, MerkleError> {
        Ok(true)
    }
}
