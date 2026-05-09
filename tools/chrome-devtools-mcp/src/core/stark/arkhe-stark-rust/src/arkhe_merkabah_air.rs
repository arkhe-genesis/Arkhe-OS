// arkhe_merkabah_air.rs — AIR do Merkabah para Winterfell

use winterfell::{
    Air, AirContext, Assertion, EvaluationFrame, ProofOptions, TraceInfo,
    TransitionConstraintDegree, math::{fields::f128::BaseElement, FieldElement, ToElements},
};
use crate::arkhe_recursive_verifier::VerifiedProof;
use pyo3::prelude::*;

const TRACE_LENGTH: usize = 128;           // 128 ciclos de execução

// ─── Public Inputs ───
#[derive(Clone, Debug)]
#[pyclass]
pub struct MerkabahInputs {
    pub node_id: [u8; 32],                 // Hash do node ID
    pub initial_phase: BaseElement,        // Fase inicial
    pub target_phase: BaseElement,         // SYNC_PHASE = 0.58π
    pub final_phase: BaseElement,          // Fase final (verificar)
    pub final_coherence: BaseElement,      // Coerência final (verificar)
}

impl MerkabahInputs {
    pub fn from_joined(joined: &VerifiedProof) -> Self {
        Self {
            node_id: joined.merkle_root,
            // These would normally be reconstructed correctly, we set them to zero for now
            // just to pass the mock compilation
            initial_phase: BaseElement::new(0),
            target_phase: BaseElement::new(0),
            final_phase: BaseElement::new(0),
            final_coherence: BaseElement::new(0),
        }
    }
}

impl ToElements<BaseElement> for MerkabahInputs {
    fn to_elements(&self) -> Vec<BaseElement> {
        vec![
            self.initial_phase,
            self.target_phase,
            self.final_phase,
            self.final_coherence,
        ]
    }
}

// ─── AIR Definition ───
pub struct MerkabahAir {
    context: AirContext<BaseElement>,
    inputs: MerkabahInputs,
}

impl Air for MerkabahAir {
    type BaseField = BaseElement;
    type PublicInputs = MerkabahInputs;

    fn new(trace_info: TraceInfo, pub_inputs: MerkabahInputs, options: ProofOptions) -> Self {
        let degrees = vec![
            TransitionConstraintDegree::new(2),  // phase transition
            TransitionConstraintDegree::new(2),  // coherence transition
            TransitionConstraintDegree::new(1),  // error definition
            TransitionConstraintDegree::new(2),  // control definition
        ];

        Self {
            context: AirContext::new(trace_info, degrees, 4, options),
            inputs: pub_inputs,
        }
    }

    fn context(&self) -> &AirContext<Self::BaseField> {
        &self.context
    }

    fn evaluate_transition<E: FieldElement + From<Self::BaseField>>(
        &self,
        frame: &EvaluationFrame<E>,
        _periodic_values: &[E],
        result: &mut [E],
    ) {
        let current = frame.current();
        let next = frame.next();

        let phase_t = current[0];
        let coherence_t = current[1];
        let error_t = current[2];
        let control_t = current[3];

        let phase_next = next[0];
        let coherence_next = next[1];
        let error_next = next[2];
        let control_next = next[3];

        // 1. phase(t+1) = phase(t) + control(t)
        result[0] = phase_next - phase_t - control_t;

        // 2. coherence(t+1) = coherence(t) + 1 * (1 - error(t)^2)
        // Note: Using integer division and scaling to mimic logic.
        let error_sq = error_t * error_t;
        result[1] = coherence_next - coherence_t - (E::ONE - error_sq);

        // 3. error(t)^2 = (phase(t) - target_phase)^2
        let target = E::from(self.inputs.target_phase);
        let diff = phase_t - target;
        result[2] = error_t * error_t - diff * diff;

        // 4. control(t+1) = -error(t+1)
        result[3] = control_next + error_next;
    }

    fn get_assertions(&self) -> Vec<Assertion<Self::BaseField>> {
        vec![
            Assertion::single(0, 0, self.inputs.initial_phase),
            Assertion::single(0, TRACE_LENGTH - 1, self.inputs.target_phase),
            Assertion::single(1, TRACE_LENGTH - 1, self.inputs.final_coherence),
            Assertion::single(2, TRACE_LENGTH - 1, BaseElement::new(0)),
        ]
    }
}
