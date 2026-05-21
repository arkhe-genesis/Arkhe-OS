use std::collections::{HashSet, HashMap};
use crate::{GHOST, LOOPSEAL, GAP_SOVEREIGN};

/// Dispute Control structure for tracking conflicts ∆*
#[derive(Debug, Clone)]
pub struct DisputeControl {
    pub n: usize,
    pub t: usize,
    /// Base conflicts ∆
    pub delta: HashSet<(String, String)>,
}

impl DisputeControl {
    pub fn new(n: usize, t: usize) -> Self {
        Self {
            n,
            t,
            delta: HashSet::new(),
        }
    }

    /// Add an accusation Pi -> Pj
    pub fn accuse(&mut self, pi: &str, pj: &str) {
        let (a, b) = if pi < pj { (pi, pj) } else { (pj, pi) };
        self.delta.insert((a.to_string(), b.to_string()));
    }

    /// Compute effective conflicts ∆* recursively
    pub fn effective_conflicts(&self) -> HashSet<(String, String)> {
        let mut delta_star = self.delta.clone();
        let mut changed = true;

        while changed {
            changed = false;
            let current_delta = delta_star.clone();

            // Build neighborhood for each node in ∆*
            let mut neighbors: HashMap<String, HashSet<String>> = HashMap::new();
            for (u, v) in &current_delta {
                neighbors.entry(u.clone()).or_default().insert(v.clone());
                neighbors.entry(v.clone()).or_default().insert(u.clone());
            }

            let nodes: Vec<String> = neighbors.keys().cloned().collect();
            for i in 0..nodes.len() {
                for j in i+1..nodes.len() {
                    let u = &nodes[i];
                    let v = &nodes[j];

                    if u == v { continue; }

                    if let (Some(u_neighbors), Some(v_neighbors)) = (neighbors.get(u), neighbors.get(v)) {
                        let union_size = u_neighbors.union(v_neighbors).count();
                        if union_size > self.t {
                            let edge = if u < v { (u.clone(), v.clone()) } else { (v.clone(), u.clone()) };
                            if delta_star.insert(edge) {
                                changed = true;
                            }
                        }
                    }
                }
            }
        }

        delta_star
    }

    /// Check if a node is isolated by counting its edges in ∆*
    pub fn is_isolated(&self, node: &str) -> bool {
        let effective = self.effective_conflicts();
        let mut conflicts = 0;
        for (u, v) in effective {
            if u == node || v == node {
                conflicts += 1;
            }
        }
        // Distance/conflicts exceed 2n/(n-t) roughly or in this model if conflicts >= n - t
        conflicts >= self.n - self.t
    }
}

/// CryptoBroadcast protocol using Block Pipeline and Dispute Control
#[derive(Debug, Clone)]
pub struct CryptoBroadcast {
    pub dispute_control: DisputeControl,
    pub block_pipeline: Vec<Vec<u8>>,
    pub dsc_depth: f64,
    pub dsp_depth: f64,
}

impl CryptoBroadcast {
    pub fn new(n: usize, t: usize) -> Self {
        Self {
            dispute_control: DisputeControl::new(n, t),
            block_pipeline: Vec::new(),
            dsc_depth: 0.0,
            dsp_depth: 0.0,
        }
    }

    /// Broadcast a block with optimal depth routing and balance checking
    pub fn broadcast(&mut self, data: Vec<u8>, sender: &str) -> Result<(), String> {
        if self.dispute_control.is_isolated(sender) {
            return Err(format!("Sender {} is isolated by Dispute Control", sender));
        }

        // Add block to pipeline
        self.block_pipeline.push(data);

        // Dsc: Increase channel depth by Loopseal
        self.dsc_depth += LOOPSEAL;
        // Dsp: Increase parties depth by Ghost
        self.dsp_depth += GHOST;

        // Balance checking (Gap Sovereign invariant)
        if self.dsc_depth > GAP_SOVEREIGN * (self.dispute_control.n as f64) {
            // Reached limit based on GAP_SOVEREIGN
            return Err("Channel depth exceeds GAP_SOVEREIGN limit".to_string());
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dispute_control_effective_conflicts() {
        // 5 nodes, threshold 1
        let mut dc = DisputeControl::new(5, 1);

        // Base conflicts
        dc.accuse("P1", "P2");
        dc.accuse("P1", "P3");
        dc.accuse("P4", "P2");
        dc.accuse("P4", "P3");

        let effective = dc.effective_conflicts();
        // P1 and P4 share neighbors P2 and P3.
        // Union size = {P2, P3} = 2 > t (which is 1).
        // Therefore, (P1, P4) should be added to effective conflicts.

        let mut found_p1_p4 = false;
        for (u, v) in effective {
            if (u == "P1" && v == "P4") || (u == "P4" && v == "P1") {
                found_p1_p4 = true;
            }
        }

        assert!(found_p1_p4, "Effective conflict between P1 and P4 not inferred");
    }

    #[test]
    fn test_crypto_broadcast_depth_metrics() {
        let mut cb = CryptoBroadcast::new(7, 4);

        assert_eq!(cb.dsc_depth, 0.0);
        assert_eq!(cb.dsp_depth, 0.0);

        let result = cb.broadcast(vec![1, 2, 3], "PG-NA");
        assert!(result.is_ok());

        assert_eq!(cb.dsc_depth, LOOPSEAL);
        assert_eq!(cb.dsp_depth, GHOST);

        // Second block
        let result = cb.broadcast(vec![4, 5, 6], "PG-NA");
        assert!(result.is_ok());

        assert_eq!(cb.dsc_depth, LOOPSEAL * 2.0);
        assert_eq!(cb.dsp_depth, GHOST * 2.0);
    }
}
