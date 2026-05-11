use crate::types::{SpacetimeGraph, Camera, DrawCommand};

pub fn render_graph(graph: &SpacetimeGraph, _camera: &Camera) -> Vec<DrawCommand> {
    let mut commands = Vec::new();
    for node in graph.visual_nodes() {
        commands.push(DrawCommand::Node(node.clone()));
    }
    for edge in graph.visual_edges() {
        // Animar arestas com curvas de Bézier baseadas nos vetores de momento
        let curve = crate::visual::physics::compute_edge_curve(edge);
        commands.push(DrawCommand::Edge(edge.clone(), curve));
    }
    commands
}
