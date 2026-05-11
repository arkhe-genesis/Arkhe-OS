use crate::engine::QArtEngine;
// Mocks para compilacao
pub struct ArtBlock;
pub struct RoyaltyEvent;
pub struct X402Bridge;

impl X402Bridge {
    pub fn send_royalty_sync(&self, _event: &RoyaltyEvent) -> Result<(), String> {
        Ok(())
    }
}

impl QArtEngine {
    pub async fn process_new_art_block_auto(
        &self,
        block: &ArtBlock,
        bridge: &std::sync::Arc<X402Bridge>,
    ) -> Vec<RoyaltyEvent> {
        let events = self.process_new_art_block(block).await.unwrap_or_default();
        for event in &events {
            if let Err(e) = bridge.send_royalty_sync(event) {
                tracing::error!("Falha ao pagar royalty: {}", e);
            }
        }
        events
    }

    // mock
    pub async fn process_new_art_block(&self, _block: &ArtBlock) -> Result<Vec<RoyaltyEvent>, ()> {
        Ok(vec![])
    }
}
