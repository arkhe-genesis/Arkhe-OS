use petgraph::graph::NodeIndex;
use nalgebra::Point3;
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ShardId(pub String);
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PortalType(pub String);

#[derive(Clone, Debug)]
pub struct VisualNode {
    pub id: NodeIndex,
    pub position: Point3<f64>,
    pub node_type: NodeType,
    pub label: String,
    pub locked: bool,
    pub scale: f64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum NodeType {
    Shard { shard_id: ShardId, motor: MotorType },
    ArtBlock { fingerprint: Vec<u8> },
    Portal { portal_type: PortalType },
    SubstrateFolder { path: String },
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum MotorType {
    ContinentalMind,
    VortexQPU,
    QArtEngine,
    FinancialValidator,
}

impl VisualNode {
    pub async fn update_financial_dashboard(&mut self) {
    }
}
