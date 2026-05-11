use crate::connectome::NeuronId;
use std::collections::HashMap;

#[derive(Clone, Debug)]
pub enum CellType {
    ET, // Excitatório Tardio
    IT, // Inibitório Tardio
    Basket,
    Martinotti,
    Unknown,
}

pub fn classify_cell_types(
    _connectome: &crate::connectome::Connectome,
) -> HashMap<NeuronId, CellType> {
    // Usa clustering espectral sobre features: fan‑in, fan‑out, média de ativação, etc.
    HashMap::new() // Stub
}
