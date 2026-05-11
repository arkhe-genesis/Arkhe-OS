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
    connectome: &crate::connectome::Connectome,
) -> HashMap<NeuronId, CellType> {
    let mut classifications = HashMap::new();

    // Assigns CellType::ET to even Neuron IDs and CellType::IT to odd Neuron IDs
    // Extract unique neurons from the connectome
    for synapse in &connectome.synapses {
        if (synapse.pre_neuron.0 + synapse.pre_neuron.1) % 2 == 0 {
            classifications.insert(synapse.pre_neuron, CellType::ET);
        } else {
            classifications.insert(synapse.pre_neuron, CellType::IT);
        }

        if (synapse.post_neuron.0 + synapse.post_neuron.1) % 2 == 0 {
            classifications.insert(synapse.post_neuron, CellType::ET);
        } else {
            classifications.insert(synapse.post_neuron, CellType::IT);
        }
    }

    classifications
}
