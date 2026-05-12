use crate::store::Store;
use crate::store::StoreError;

const ZK_PREFIX: &[u8] = b"zk:";

impl Store {
    pub fn put_zk_proof(&mut self, proof_hash: &[u8], proof: &[u8]) -> Result<(), StoreError> {
        let mut key = Vec::from(ZK_PREFIX);
        key.extend_from_slice(proof_hash);
        self.put(&key, proof)
    }

    pub fn get_zk_proof(&mut self, proof_hash: &[u8]) -> Option<Vec<u8>> {
        let mut key = Vec::from(ZK_PREFIX);
        key.extend_from_slice(proof_hash);
        self.get(&key)
    }
}
