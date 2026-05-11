use crate::cell_types::classify_cell_types;
use crate::connectome::Connectome;
use crate::mapper::{ContinentalMind, Mapper};
use crate::proofreader::{ActivationRecord, Proofreader};
use crate::wiring_rules::extract_wiring_rules;

pub struct NeuralCartographer {
    pub proofreader: Proofreader,
}

impl NeuralCartographer {
    pub fn new(proofreader: Proofreader) -> Self {
        Self { proofreader }
    }

    pub fn process_model(
        &mut self,
        model: &ContinentalMind,
        activations: &ActivationRecord,
    ) -> Connectome {
        // 1. Extrai conectoma atual do modelo.
        let mut connectome = Mapper::extract_connectome(model);

        // 2. Aplica proofreading automático.
        self.proofreader
            .auto_proofread(&mut connectome, activations);

        // 3. Classifica tipos celulares.
        let cell_types = classify_cell_types(&connectome);

        // 4. Extrai regras de ligação.
        let _rules = extract_wiring_rules(&connectome, &cell_types);

        // 5-8. (Stub) Gera Plano de Re‑wireamento, aplica, testa, registra na TemporalChain.
        connectome
    }
}
