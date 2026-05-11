use crate::cell_types::CellType;
use crate::connectome::NeuronId;
use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct WiringRule {
    pub description: String,
}

pub fn extract_wiring_rules(
    _connectome: &crate::connectome::Connectome,
    _cell_types: &HashMap<NeuronId, CellType>,
) -> Vec<WiringRule> {
    // Para cada par de tipos, calcula a probabilidade de conexão em relação ao esperado ao acaso.
    Vec::new() // Stub
}
