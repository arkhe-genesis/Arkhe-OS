use crate::{QArtEngine, ArtBlock, TemporalChain};
use std::sync::Arc;
use crate::compensation::x402_pix_bridge::X402PixBridge;

pub struct AutoRoyaltyService {
    engine: QArtEngine,
    bridge: Arc<X402PixBridge>,
    chain: Arc<TemporalChain>,
}

impl AutoRoyaltyService {
    pub fn new(engine: QArtEngine, bridge: Arc<X402PixBridge>, chain: Arc<TemporalChain>) -> Self {
        Self { engine, bridge, chain }
    }

    /// Runs forever, scanning new ArtBlocks and paying royalties.
    pub async fn run(&self) {
        let mut last_block = self.chain.head_height().await;
        loop {
            if let Ok(new_blocks) = self.chain.get_blocks_since(last_block).await {
                for block in new_blocks {
                    if block.is_art_block() {
                        let art_block: ArtBlock = block.into();
                        let events = self.engine.process_new_art_block(&art_block).await.unwrap_or_default();
                        for event in &events {
                            if let Err(e) = self.bridge.send_royalty_sync(event) {
                                tracing::error!("Royalty payment failed: {}", e);
                            }
                        }
                    }
                }
                last_block = self.chain.head_height().await;
            }
            tokio::time::sleep(std::time::Duration::from_secs(5)).await;
        }
    }
}
