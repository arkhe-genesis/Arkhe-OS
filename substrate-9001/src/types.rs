
use crate::visual::node::VisualNode;

pub struct ShardId;
pub struct PortalType;

pub struct TemporalHashChain {}
impl TemporalHashChain {
    pub fn query_events<T>(&self) -> Vec<T> { vec![] }
}

pub struct RoyaltyEvent {}

pub struct SpacetimeGraph {}
impl SpacetimeGraph {
    pub fn visual_nodes(&self) -> Vec<&VisualNode> { vec![] }
    pub fn visual_edges(&self) -> Vec<&Edge> { vec![] }
}

pub struct Camera {}

pub enum DrawCommand {
    Node(VisualNode),
    Edge(Edge, Curve),
}

#[derive(Clone)]
pub struct Edge {}

pub struct Curve {}
