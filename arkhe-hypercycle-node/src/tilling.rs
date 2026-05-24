use crate::invariants::GHOST;
use chrono::{DateTime, Utc};
use sha3::{Sha3_256, Digest};
use std::collections::{HashMap, HashSet};

pub type Conflict = (usize, usize);

#[derive(Debug, Clone)]
pub struct Virtues {
    pub courage: f64,    // uptime — persistência operacional
    pub wisdom: f64,     // computation × reputation — eficiência com qualidade
    pub compassion: f64, // cooperação — bounties + revisões
}

#[derive(Debug, Clone)]
pub struct TillingScore {
    pub score: f64,
    pub virtues: Virtues,
    pub temporal_factor: f64,
    pub can_unlock_node: bool,  // score ≥ 2.0 (HyperCycle)
    pub can_settle: bool,       // score ≥ GHOST (Arkhe)
}

pub struct TillingEngine {
    uptime_seconds: f64,
    computations_completed: u64,
    reputation: f64,
    bounties_settled: u64,
    reviews_approved: u64,
    registration_date: DateTime<Utc>,
}

impl TillingEngine {
    pub fn new(initial_reputation: f64, reg_date: DateTime<Utc>) -> Self {
        Self {
            uptime_seconds: 0.0,
            computations_completed: 0,
            reputation: initial_reputation.clamp(0.0, 1.0),
            bounties_settled: 0,
            reviews_approved: 0,
            registration_date: reg_date,
        }
    }

    pub fn record_activity(&mut self, uptime_delta_s: f64, computations: u64,
                           bounties: u64, reviews: u64) {
        self.uptime_seconds += uptime_delta_s;
        self.computations_completed += computations;
        self.bounties_settled += bounties;
        self.reviews_approved += reviews;
        self.reputation = (self.reputation + 0.01 * reviews as f64).min(1.0);
    }

    pub fn compute(&self) -> TillingScore {
        let uptime_norm = (self.uptime_seconds / 3600.0).min(1.0);
        let comp_norm = (self.computations_completed as f64 / 100.0).min(1.0);
        let bounties_norm = (self.bounties_settled as f64 / 10.0).min(1.0);
        let reviews_norm = (self.reviews_approved as f64 / 20.0).min(1.0);

        let courage = uptime_norm;
        let wisdom = comp_norm * self.reputation;
        let compassion = (bounties_norm + reviews_norm) / 2.0;

        let base_score = (courage + wisdom + compassion) / 3.0;

        let days = (Utc::now() - self.registration_date).num_days() as f64;
        let temporal_factor = 1.0 + (days / 540.0).min(1.0);

        let score = base_score * temporal_factor;

        TillingScore {
            score,
            virtues: Virtues { courage, wisdom, compassion },
            temporal_factor,
            can_unlock_node: score >= 2.0,
            can_settle: score >= GHOST,
        }
    }

    pub fn merkle_leaf(&self) -> String {
        let score = self.compute();
        let input = format!("{}:{}:{}:{}", score.score, score.virtues.courage,
                           score.virtues.wisdom, score.virtues.compassion);
        hex::encode(Sha3_256::digest(input.as_bytes()))
    }
}
#[derive(Debug, Clone)]
pub struct DisputeAwareTilling {
    pub tilling_score: f64,
    pub delta_star: HashSet<Conflict>,  // conflitos efetivos
    pub isolated: bool,
}

impl DisputeAwareTilling {
    /// Reporta um resultado de workload e verifica consistência com outros nós.
    pub fn report_result(&mut self, node_id: usize, result_hash: &[u8],
                         peer_results: &HashMap<usize, Vec<u8>>) {
        // Compara com os resultados dos pares
        for (&peer_id, peer_hash) in peer_results {
            if peer_id != node_id && peer_hash != result_hash {
                // Adiciona conflito entre este nó e o peer
                let conflict = (node_id.min(peer_id), node_id.max(peer_id));
                self.delta_star.insert(conflict);
            }
        }
        // Inferir ∆* como no artigo: se dois partidos juntos têm mais de t conflitos, conflito entre eles
        let t = 45; // threshold de corrupção para 59 nós
        let mut new_delta = self.delta_star.clone();
        let mut changed = true;
        while changed {
            changed = false;
            for i in 0..59 {
                for j in i+1..59 {
                    if !new_delta.contains(&(i,j)) {
                        let conflicts_i: HashSet<usize> = new_delta.iter()
                            .filter(|(a,b)| *a == i || *b == i)
                            .map(|(a,b)| if *a == i { *b } else { *a })
                            .collect();
                        let conflicts_j: HashSet<usize> = new_delta.iter()
                            .filter(|(a,b)| *a == j || *b == j)
                            .map(|(a,b)| if *a == j { *b } else { *a })
                            .collect();
                        let union_size = conflicts_i.union(&conflicts_j).count();
                        if union_size > t {
                            new_delta.insert((i,j));
                            changed = true;
                        }
                    }
                }
            }
        }
        self.delta_star = new_delta;
        // Se o nó está em conflito com mais de t outros, isola‑o
        let conflicts_with_node = self.delta_star.iter()
            .filter(|(a,b)| *a == node_id || *b == node_id)
            .count();
        if conflicts_with_node > t {
            self.isolated = true;
            self.tilling_score *= 0.5; // penaliza o Tilling Score
        }
    }
}
