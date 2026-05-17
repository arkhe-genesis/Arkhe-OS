use arkp_state::{InMemoryRepository, StateRepositoryExt};
use arkp_telecom::{OrbitalMeshBridge, SkyBridge};
use std::sync::Arc;

#[tokio::test]
async fn test_full_integration() {
    let state = Arc::new(InMemoryRepository::new());

    state.set("test_key", "test_value").await.unwrap();
    let val: Option<String> = state.get("test_key").await;
    assert_eq!(val, Some("test_value".to_string()));

    let bridge = OrbitalMeshBridge::new("orbital://mesh.arkhe");
    bridge.connect().await.unwrap();
    let status = bridge.status().await.unwrap();
    assert!(status.connected);
}
