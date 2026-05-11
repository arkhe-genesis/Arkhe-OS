use serde::{Deserialize, Serialize};

/// Identificador único de neurônio (layer, index)
#[derive(Clone, Copy, Hash, Eq, PartialEq, Serialize, Deserialize, Debug)]
pub struct NeuronId(pub usize, pub usize);

/// Representa uma sinapse entre duas unidades
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Synapse {
    pub pre_neuron: NeuronId,
    pub post_neuron: NeuronId,
    pub weight: f64,
    pub activation_correlation: f64, // similar à correlação funcional do paper
    pub is_excitatory: bool,         // peso > 0 → excitatório
    pub layer: usize,
    pub head: Option<usize>, // para attention heads
}

#[derive(Default, Clone, Debug, Serialize, Deserialize)]
pub struct Connectome {
    pub synapses: Vec<Synapse>,
}

impl Connectome {
    pub fn new() -> Self {
        Self {
            synapses: Vec::new(),
        }
    }

    pub fn add_synapse(&mut self, synapse: Synapse) {
        self.synapses.push(synapse);
    }

    pub fn split_neuron_pair(&mut self, _a: NeuronId, _b: NeuronId) {
        // TODO: Implement split logic
    }

    pub fn merge_neuron_pair(&mut self, _a: NeuronId, _b: NeuronId) {
        // TODO: Implement merge logic
    }

    pub fn prune_weak_synapses(&mut self, min_weight: f64) {
        self.synapses.retain(|s| s.weight.abs() >= min_weight);
    }
}
