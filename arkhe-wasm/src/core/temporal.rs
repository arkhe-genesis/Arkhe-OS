use core::fmt;
use core::ops::{Add, Sub, Mul, Div, Neg};
use crate::crypto::keccak::keccak256;

#[repr(C)]
#[derive(Copy, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Address([u8; 32]);

impl Address {
    pub const ZERO: Self = Self([0u8; 32]);
    pub fn new(s: &str) -> Self { Self(keccak256(s.as_bytes())) }
    pub const fn from_bytes(bytes: [u8; 32]) -> Self { Self(bytes) }
    pub fn as_bytes(&self) -> &[u8; 32] { &self.0 }
    pub fn short(&self) -> [u8; 8] {
        let mut out = [0u8; 8];
        out.copy_from_slice(&self.0[..8]);
        out
    }
}
impl fmt::Debug for Address {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "0x{}", hex::encode(&self.0[..8]))
    }
}

#[repr(transparent)]
#[derive(Copy, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Default)]
pub struct Fixed(pub i32);

impl Fixed {
    pub const ZERO: Self = Self(0);
    pub const ONE: Self = Self(1 << 16);
    pub const HALF: Self = Self(1 << 15);
    pub const MAX: Self = Self(i32::MAX);
    pub const MIN: Self = Self(i32::MIN);
    pub const fn from_int(n: i32) -> Self { Self(n << 16) }
    pub fn from_float(f: f64) -> Self { Self((f * 65536.0) as i32) }
    pub fn to_float(self) -> f64 { self.0 as f64 / 65536.0 }
    pub fn mul(self, other: Self) -> Self {
        let result = (self.0 as i64) * (other.0 as i64);
        Self((result >> 16) as i32)
    }
    pub fn div(self, other: Self) -> Self {
        if other.0 == 0 {
            return if self.0 >= 0 { Self::MAX } else { Self::MIN };
        }
        let result = ((self.0 as i64) << 16) / (other.0 as i64);
        Self(result as i32)
    }
    pub fn inv(self) -> Self { Self::ONE.div(self) }
    pub fn abs(self) -> Self { if self.0 < 0 { Self(-self.0) } else { self } }
    pub fn min(self, other: Self) -> Self { if self < other { self } else { other } }
    pub fn max(self, other: Self) -> Self { if self > other { self } else { other } }
    pub fn saturating_add(self, other: Self) -> Self { Self(self.0.saturating_add(other.0)) }
    pub fn saturating_sub(self, other: Self) -> Self { Self(self.0.saturating_sub(other.0)) }
}
impl Add for Fixed {
    type Output = Self;
    fn add(self, other: Self) -> Self { Self(self.0 + other.0) }
}
impl Sub for Fixed {
    type Output = Self;
    fn sub(self, other: Self) -> Self { Self(self.0 - other.0) }
}
impl Neg for Fixed {
    type Output = Self;
    fn neg(self) -> Self { Self(-self.0) }
}

#[repr(C)]
#[derive(Clone)]
pub struct TemporalMessage {
    pub id_offset: u16,
    pub id_len: u16,
    pub sender: Address,
    pub receiver: Address,
    pub source_ts: i64,
    pub target_ts: i64,
    pub content_offset: u32,
    pub content_len: u32,
    pub payload_ptr: u32,
    pub payload_len: u32,
    pub consistency_score: Fixed,
    pub violations_count: u16,
    pub paradox_type: u8,
    pub sig_offset: u32,
    pub sig_len: u16,
    pub zk_offset: u32,
    pub zk_len: u16,
}

impl TemporalMessage {
    pub fn hash(&self, data: &[u8]) -> Address {
        let start = self.content_offset as usize;
        let end = self.content_offset as usize + self.content_len as usize;
        Address::new(core::str::from_utf8(&data[start..end]).unwrap_or(""))
    }
    pub fn is_temporally_valid(&self, now: i64) -> bool {
        self.source_ts <= now && self.target_ts >= now
    }
    pub fn causal_precedes(&self, other: &Self) -> bool {
        self.target_ts <= other.source_ts
    }
}

#[repr(C)]
pub struct TemporalBlock {
    pub index: u64,
    pub prev_hash: Address,
    pub timestamp: i64,
    pub state_root: Address,
    pub oracle_root: Address,
    pub validator_sig_offset: u32,
    pub validator_sig_len: u16,
    pub messages_offset: u32,
    pub messages_count: u32,
    pub messages_size: u32,
}

impl TemporalBlock {
    pub fn hash(&self) -> Address {
        let mut data = [0u8; 128];
        data[..8].copy_from_slice(&self.index.to_be_bytes());
        data[8..40].copy_from_slice(self.prev_hash.as_bytes());
        data[40..48].copy_from_slice(&self.timestamp.to_be_bytes());
        data[48..80].copy_from_slice(self.state_root.as_bytes());
        data[80..112].copy_from_slice(self.oracle_root.as_bytes());
        data[112..116].copy_from_slice(&self.messages_count.to_be_bytes());
        Address(keccak256(&data))
    }
}

pub const BLOCK_INTERVAL_NSEC: i64 = 10_000_000_000;
pub const MAX_MESSAGES_PER_BLOCK: u32 = 8192;
pub const CONSISTENCY_THRESHOLD: Fixed = Fixed(55705); // 0.85 * 65536
pub const PARADOX_SCORE: Fixed = Fixed(19660); // 0.30 * 65536

#[repr(C)]
pub struct NetworkConfig {
    pub block_interval: i64,
    pub max_messages: u32,
    pub consistency_threshold: Fixed,
    pub paranoid: bool,
}

impl Default for NetworkConfig {
    fn default() -> Self {
        Self {
            block_interval: BLOCK_INTERVAL_NSEC,
            max_messages: MAX_MESSAGES_PER_BLOCK,
            consistency_threshold: CONSISTENCY_THRESHOLD,
            paranoid: false,
        }
    }
}
