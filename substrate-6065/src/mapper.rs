use crate::connectome::{Connectome, NeuronId, Synapse};

pub const MIN_WEIGHT_THRESHOLD: f64 = 0.01;

// Stub for ContinentalMind layer
pub struct ContinentalMindLayer {
    pub weight: Vec<Vec<f64>>,
}

// Stub for ContinentalMind model
pub struct ContinentalMind {
    pub layers: Vec<ContinentalMindLayer>,
}

pub struct Mapper;

impl Mapper {
    pub fn extract_connectome(model: &ContinentalMind) -> Connectome {
        let mut connectome = Connectome::new();
        for (layer_idx, layer) in model.layers.iter().enumerate() {
            // Para cada peso na camada
            for (i, row) in layer.weight.iter().enumerate() {
                for (j, &w) in row.iter().enumerate() {
                    if w.abs() > MIN_WEIGHT_THRESHOLD {
                        connectome.add_synapse(Synapse {
                            pre_neuron: NeuronId(layer_idx, i),
                            post_neuron: NeuronId(layer_idx + 1, j),
                            weight: w,
                            activation_correlation: 0., // preenchido depois
                            is_excitatory: w > 0.,
                            layer: layer_idx,
                            head: None,
                        });
                    }
                }
            }
        }
        connectome
    }
}
