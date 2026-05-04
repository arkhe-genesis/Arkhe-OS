use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct QhttpPacket {
    pub quantum_header: QuantumHeader,
    pub intention_hash: [u8; 32],
    pub sato_payload: SATOPayload,
    pub plank_bytecode: Vec<u8>,
    pub coherence_signature: CoherenceSignature,
    pub ghz_footer: GHZFooter,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct QuantumHeader {
    pub bell_state: BellState,
    pub measurement_basis: Basis,
    pub timestamp: u64,
    pub channel_id: u8,
    pub sequence_number: u32,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub enum BellState {
    PhiPlus, PhiMinus, PsiPlus, PsiMinus
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub enum Basis {
    Computational, Diagonal
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct SATOPayload {
    pub vertex_tokens: Vec<VertexToken>,
    pub uv_islands: Vec<UVIsland>,
    pub topology_meta: TopologyMetadata,
    pub sato_checksum: [u8; 32],
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct VertexToken {
    pub x: i16, pub y: i16, pub z: i16,
    pub u: Option<i16>, pub v: Option<i16>,
    pub flags: u8,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct UVIsland {
    pub id: u32,
    pub vertices: Vec<usize>,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct TopologyMetadata {
    pub stride: u8,
    pub mode: u8,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct CoherenceSignature {
    pub m_value: u16,
    pub phase: u64,
    pub tau_hash: [u8; 32],
    pub node_signature: Vec<u8>, // Using Vec for large arrays as serde doesn't support [u8; 65] natively
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct GHZFooter {
    pub entanglement_witness: EntanglementWitness,
    pub quantum_mac: [u8; 32],
    pub merkle_root: [u8; 32],
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct EntanglementWitness {
    pub xx_correlation: f64,
    pub zz_correlation: f64,
}
