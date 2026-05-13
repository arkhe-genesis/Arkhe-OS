
use crate::types::*;
use crate::errors::*;

pub trait TemporalChainInterface: Send + Sync {
    fn read_block(&self, block_number: u64) -> Result<TemporalBlock, QipError>;
    fn query_fingerprints_in_block(&self, block_number: u64) -> Result<Vec<DataFingerprint>, QipError>;
}

pub struct QuantumIPEngine {}
