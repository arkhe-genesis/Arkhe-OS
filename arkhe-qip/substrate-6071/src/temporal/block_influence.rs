use std::collections::{HashMap, HashSet};
use serde::{Serialize, Deserialize};

use crate::types::{DataFingerprint, TemporalBlock, InfluenceResult};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct BlockInfluence {
    pub block_number: u64,
}
