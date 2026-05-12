use crate::CellState;

pub struct DataValuation;

impl DataValuation {
    pub fn compute(&self, _cell: &CellState, _query_hash: &[u8]) -> f64 {
        0.01 // dummy value
    }
}
