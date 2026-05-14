
use async_trait::async_trait;
use serde::{de::DeserializeOwned, Serialize};
use std::collections::HashMap;

// We remove the generic methods from the trait and move them to an extension trait or make the methods operate on Vec<u8> directly.
// The task asks to have `dyn StateRepository`, so we must make the trait dyn-compatible.

#[async_trait]
pub trait StateRepository: Send + Sync {
    async fn get_bytes(&self, key: &str) -> Option<Vec<u8>>;
    async fn set_bytes(&self, key: &str, value: Vec<u8>) -> Result<(), StateError>;
    async fn delete(&self, key: &str) -> Result<(), StateError>;
    async fn keys(&self) -> Vec<String>;
}

#[async_trait]
pub trait StateRepositoryExt {
    async fn get<T: DeserializeOwned + Send>(&self, key: &str) -> Option<T>;
    async fn set<T: Serialize + Send + Sync>(&self, key: &str, value: T) -> Result<(), StateError>;
}

#[async_trait]
impl<R: StateRepository + ?Sized> StateRepositoryExt for R {
    async fn get<T: DeserializeOwned + Send>(&self, key: &str) -> Option<T> {
        let bytes = self.get_bytes(key).await?;
        serde_json::from_slice(&bytes).ok()
    }

    async fn set<T: Serialize + Send + Sync>(&self, key: &str, value: T) -> Result<(), StateError> {
        let serialized = serde_json::to_vec(&value)
            .map_err(|e| StateError::Serde(e.to_string()))?;
        self.set_bytes(key, serialized).await
    }
}

#[derive(Debug, thiserror::Error)]
pub enum StateError {
    #[error("[STATE-001] Serialization error: {0}")]
    Serde(String),
    #[error("[STATE-002] IO: {0}")]
    Io(String),
}

pub struct InMemoryRepository {
    data: tokio::sync::RwLock<HashMap<String, Vec<u8>>>,
}

impl InMemoryRepository {
    pub fn new() -> Self {
        Self { data: tokio::sync::RwLock::new(HashMap::new()) }
    }
}

#[async_trait]
impl StateRepository for InMemoryRepository {
    async fn get_bytes(&self, key: &str) -> Option<Vec<u8>> {
        let data = self.data.read().await;
        data.get(key).cloned()
    }
    async fn set_bytes(&self, key: &str, value: Vec<u8>) -> Result<(), StateError> {
        self.data.write().await.insert(key.to_string(), value);
        Ok(())
    }
    async fn delete(&self, key: &str) -> Result<(), StateError> {
        self.data.write().await.remove(key);
        Ok(())
    }
    async fn keys(&self) -> Vec<String> {
        self.data.read().await.keys().cloned().collect()
    }
}
