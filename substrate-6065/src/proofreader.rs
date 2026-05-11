use crate::connectome::{Connectome, NeuronId};

pub struct ActivationRecord {}

pub struct MergePair {
    pub a: NeuronId,
    pub b: NeuronId,
}

pub struct SplitPair {
    pub a: NeuronId,
    pub b: NeuronId,
}

pub struct Proofreader {
    pub similarity_threshold: f64,
    pub min_activation_variance: f64,
    pub min_weight: f64,
}

impl Proofreader {
    pub fn auto_proofread(&mut self, connectome: &mut Connectome, activations: &ActivationRecord) {
        // 1. Detectar merges: neurônios com correlação > 0.95 e sem separação funcional
        let merges = self.detect_merges(connectome, activations);
        for merge in &merges {
            connectome.split_neuron_pair(merge.a, merge.b);
        }

        // 2. Detectar splits: fragmentos de neurônio que deveriam ser unidos
        let splits = self.detect_splits(connectome, activations);
        for split in &splits {
            connectome.merge_neuron_pair(split.a, split.b);
        }

        // 3. Remover sinapses fantasmas (pesos abaixo do ruído)
        connectome.prune_weak_synapses(self.min_weight);

        // 4. Registrar edições como eventos na TemporalChain
        self.log_edits(&merges, &splits);
    }

    fn detect_merges(
        &self,
        _connectome: &Connectome,
        _activations: &ActivationRecord,
    ) -> Vec<MergePair> {
        Vec::new() // Stub
    }

    fn detect_splits(
        &self,
        _connectome: &Connectome,
        _activations: &ActivationRecord,
    ) -> Vec<SplitPair> {
        Vec::new() // Stub
    }

    fn log_edits(&self, _merges: &[MergePair], _splits: &[SplitPair]) {
        // Stub
    }
}
