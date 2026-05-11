use crate::store::Store;
use crate::store::StoreError;

const BLOCK_PREFIX: &[u8] = b"block:";

impl Store {
    pub fn put_block(&mut self, height: u64, block: &[u8]) -> Result<(), StoreError> {
        let mut key = Vec::from(BLOCK_PREFIX);
        key.extend_from_slice(&height.to_be_bytes());
        self.put(&key, block)
    }

    pub fn get_block(&mut self, height: u64) -> Option<Vec<u8>> {
        let mut key = Vec::from(BLOCK_PREFIX);
        key.extend_from_slice(&height.to_be_bytes());
        self.get(&key)
    }
}
