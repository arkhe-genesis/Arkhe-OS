use rusty_leveldb::{DB, Options, LdbIterator, DBIterator};
use std::path::Path;

pub struct Store {
    db: DB,
}

impl Store {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self, StoreError> {
        let opt = Options::default();
        let db = DB::open(path, opt)?;
        Ok(Self { db })
    }

    pub fn put(&mut self, key: &[u8], value: &[u8]) -> Result<(), StoreError> {
        self.db.put(key, value)?;
        Ok(())
    }

    pub fn get(&mut self, key: &[u8]) -> Option<Vec<u8>> {
        self.db.get(key)
    }

    pub fn delete(&mut self, key: &[u8]) -> Result<(), StoreError> {
        self.db.delete(key)?;
        Ok(())
    }

    pub fn iterator(&mut self) -> StoreIterator {
        let mut iter = self.db.new_iter().unwrap();
        let is_valid = iter.valid() || {
            iter.seek_to_first();
            iter.valid()
        };
        StoreIterator { iter, is_valid }
    }

    pub fn flush(&mut self) -> Result<(), StoreError> {
        self.db.flush()?;
        Ok(())
    }
}

#[derive(Debug, thiserror::Error)]
pub enum StoreError {
    #[error("LevelDB error: {0}")]
    LevelDB(#[from] rusty_leveldb::Status),
}

pub struct StoreIterator {
    iter: DBIterator,
    is_valid: bool,
}

impl Iterator for StoreIterator {
    type Item = (Vec<u8>, Vec<u8>);

    fn next(&mut self) -> Option<Self::Item> {
        if !self.is_valid {
            return None;
        }

        let mut k = Vec::new();
        let mut v = Vec::new();

        if self.iter.current(&mut k, &mut v) {
            self.is_valid = self.iter.advance();
            Some((k, v))
        } else {
            None
        }
    }
}
