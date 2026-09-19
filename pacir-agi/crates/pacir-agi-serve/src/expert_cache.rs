use pacir_agi_core::ArkheResult;
use std::collections::{HashMap, VecDeque};
pub struct ExpertCache {
    experts: HashMap<u64, Vec<f32>>,
    order: VecDeque<u64>,
    max_size: usize,
    hits: u64,
    misses: u64,
}
impl ExpertCache {
    pub fn new(max_size: usize) -> Self {
        Self {
            experts: HashMap::new(),
            order: VecDeque::new(),
            max_size,
            hits: 0,
            misses: 0,
        }
    }
    pub async fn get_or_fetch(&mut self, id: u64) -> ArkheResult<Vec<f32>> {
        if let Some(v) = self.experts.get(&id) {
            self.hits += 1;
            return Ok(v.clone());
        }
        self.misses += 1;
        let value = vec![0.; 4096];
        if self.max_size > 0 {
            if self.experts.len() == self.max_size {
                if let Some(old) = self.order.pop_front() {
                    self.experts.remove(&old);
                }
            }
            self.order.push_back(id);
            self.experts.insert(id, value.clone());
        }
        Ok(value)
    }
    pub fn stats(&self) -> (u64, u64, f64) {
        let n = self.hits + self.misses;
        (
            self.hits,
            self.misses,
            if n == 0 {
                0.
            } else {
                self.hits as f64 / n as f64
            },
        )
    }
}
