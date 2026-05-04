use std::collections::HashMap;

pub type NodeId = String;

pub struct MWeightedRouter {
    pub neighbor_m: HashMap<NodeId, f64>,
}

impl MWeightedRouter {
    pub fn new() -> Self {
        Self {
            neighbor_m: HashMap::new(),
        }
    }

    pub fn select_next_hop(&self, _intention_hash: &[u8; 32], _target_m: u16) -> NodeId {
        // Ponderação baseada em M
        if self.neighbor_m.is_empty() {
            return "fallback".to_string();
        }

        self.neighbor_m.iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
            .map(|(id, _)| id.clone())
            .unwrap_or_else(|| "fallback".to_string())
    }

    pub fn update_neighbor_m(&mut self, node: NodeId, measured_m: f64) {
        let alpha = 0.3;
        let current = *self.neighbor_m.get(&node).unwrap_or(&measured_m);
        let smoothed = alpha * measured_m + (1.0 - alpha) * current;
        self.neighbor_m.insert(node, smoothed);
    }
}
