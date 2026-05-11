use petgraph::graph::NodeIndex;
use nalgebra::Point3;
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VisualNode {
    pub id: NodeIndex,
    pub position: Point3<f64>,
    pub node_type: NodeType,
    pub label: String,
    pub locked: bool,      // Se trava posição
    pub scale: f64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum NodeType {
    Shard { shard_id: String, motor: MotorType },
    ArtBlock { fingerprint: Vec<u8> },
    Portal { portal_type: String },
    SubstrateFolder { path: String },
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum MotorType {
    ContinentalMind,
    VortexQPU,
    QArtEngine,
    FinancialValidator,
    // ... outros
}

pub struct PortalNode {
    pub dashboard_data: Vec<crate::types::RoyaltyEvent>,
}

impl PortalNode {
    pub async fn update_financial_dashboard(&mut self, _chain: &crate::types::TemporalHashChain) {
        // let recent_payments = chain.query_events::<RoyaltyEvent>(/* last 100 blocks */);
        // self.dashboard_data = recent_payments;
    }
}
