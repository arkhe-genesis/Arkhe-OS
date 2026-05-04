use tokio::sync::mpsc;
use qhttp_protocol::QhttpPacket;

pub struct QhttpNode {
    pub node_id: String,
    pub coherence_m: f64,
    pub packet_rx: mpsc::Receiver<QhttpPacket>,
    pub packet_tx: mpsc::Sender<QhttpPacket>,
}

impl QhttpNode {
    pub fn new(node_id: String, rx: mpsc::Receiver<QhttpPacket>, tx: mpsc::Sender<QhttpPacket>) -> Self {
        Self {
            node_id,
            coherence_m: 0.95,
            packet_rx: rx,
            packet_tx: tx,
        }
    }

    pub async fn run(&mut self) {
        while let Some(packet) = self.packet_rx.recv().await {
            self.process_incoming(packet).await;
        }
    }

    async fn process_incoming(&mut self, packet: QhttpPacket) {
        // Simplified verification
        if packet.coherence_signature.m_value > 800 {
            println!("Node {} processing packet with M={}", self.node_id, packet.coherence_signature.m_value);
        }
    }
}
