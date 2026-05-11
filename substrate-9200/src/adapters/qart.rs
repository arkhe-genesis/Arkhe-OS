use crate::store::Store;
use crate::store::StoreError;

const ART_PREFIX: &[u8] = b"art:";

impl Store {
    pub fn put_art_fingerprint(&mut self, fp_hash: &[u8], block: &[u8]) -> Result<(), StoreError> {
        let mut key = Vec::from(ART_PREFIX);
        key.extend_from_slice(fp_hash);
        self.put(&key, block)
    }

    pub fn get_art_by_fingerprint(&mut self, fp_hash: &[u8]) -> Option<Vec<u8>> {
        let mut key = Vec::from(ART_PREFIX);
        key.extend_from_slice(fp_hash);
        self.get(&key)
    }
}
