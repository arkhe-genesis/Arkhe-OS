// lib.rs — Bindings Python para Winterfell via PyO3

use pyo3::prelude::*;
use winterfell::{
    StarkProof, ProofOptions, FieldExtension, TraceTable, verify, TraceInfo, Prover,
    math::fields::f128::BaseElement,
};

mod arkhe_merkabah_air;
mod arkhe_recursive_verifier;

use arkhe_merkabah_air::{MerkabahAir, MerkabahInputs};
use arkhe_recursive_verifier::RecursiveJoinCircuit;

/// Gera uma proof STARK para um nó Merkabah
#[pyfunction]
fn generate_merkabah_proof(
    node_id: [u8; 32],
    initial_phase: f64,
    target_phase: f64,
    trace_data: Vec<Vec<f64>>,
) -> PyResult<Vec<u8>> {
    // Mapeamento f64 -> f128 fields
    // Em produção, isso usaria um fixed-point. Para o MVP de escala (escalonamos f64 por 1000).
    let scale = 1000.0;
    let inputs = MerkabahInputs {
        node_id,
        initial_phase: BaseElement::new((initial_phase * scale) as u128),
        target_phase: BaseElement::new((target_phase * scale) as u128),
        final_phase: BaseElement::new((trace_data.last().unwrap()[0] * scale) as u128),
        final_coherence: BaseElement::new((trace_data.last().unwrap()[1] * scale) as u128),
    };

    let options = ProofOptions::new(
        80,                     // num_queries
        8,                      // blowup_factor
        16,                     // grinding_factor
        FieldExtension::Quadratic,
        8,                      // FRI folding_factor
        255,                    // FRI max_remainder_size
    );

    let num_rows = trace_data.len();
    if num_rows < 128 {
        return Err(pyo3::exceptions::PyValueError::new_err("Trace must be at least 128 steps long"));
    }
    let num_cols = trace_data[0].len();
    let mut columns: Vec<Vec<BaseElement>> = vec![vec![BaseElement::new(0); num_rows]; num_cols];

    for (row_idx, row) in trace_data.iter().enumerate() {
        for (col_idx, &val) in row.iter().enumerate() {
            // Emulating the fixed point conversion.
            columns[col_idx][row_idx] = BaseElement::new((val * scale) as u128);
        }
    }

    let trace = TraceTable::init(columns);

    struct MerkabahProver {
        options: ProofOptions,
        inputs: MerkabahInputs,
    }

    impl Prover for MerkabahProver {
        type BaseField = BaseElement;
        type Air = MerkabahAir;
        type Trace = TraceTable<BaseElement>;
        type HashFn = winterfell::crypto::hashers::Blake3_256<BaseElement>;
        type RandomCoin = winterfell::crypto::DefaultRandomCoin<Self::HashFn>;
        type TraceLde<E: winterfell::math::FieldElement<BaseField = Self::BaseField>> = winterfell::DefaultTraceLde<E, Self::HashFn>;
        type ConstraintEvaluator<'a, E: winterfell::math::FieldElement<BaseField = Self::BaseField>> = winterfell::DefaultConstraintEvaluator<'a, Self::Air, E>;

        fn get_pub_inputs(&self, _trace: &Self::Trace) -> MerkabahInputs {
            self.inputs.clone()
        }

        fn options(&self) -> &ProofOptions {
            &self.options
        }

        fn new_trace_lde<E: winterfell::math::FieldElement<BaseField = Self::BaseField>>(&self, trace_info: &TraceInfo, main_trace: &winterfell::matrix::ColMatrix<Self::BaseField>, domain: &winterfell::StarkDomain<Self::BaseField>) -> (Self::TraceLde<E>, winterfell::TracePolyTable<E>) {
            winterfell::DefaultTraceLde::new(trace_info, main_trace, domain)
        }

        fn new_evaluator<'a, E: winterfell::math::FieldElement<BaseField = Self::BaseField>>(&self, air: &'a Self::Air, aux_rand_elements: winterfell::AuxTraceRandElements<E>, composition_coefficients: winterfell::ConstraintCompositionCoefficients<E>) -> Self::ConstraintEvaluator<'a, E> {
            winterfell::DefaultConstraintEvaluator::new(air, aux_rand_elements, composition_coefficients)
        }
    }

    let prover = MerkabahProver { options, inputs };
    let proof = prover.prove(trace)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Proof generation failed: {:?}", e)))?;

    Ok(proof.to_bytes())
}

/// Verifica uma proof STARK
#[pyfunction]
fn verify_merkabah_proof(proof_bytes: Vec<u8>, inputs: MerkabahInputs) -> PyResult<bool> {
    let proof = StarkProof::from_bytes(&proof_bytes)
        .map_err(|_| pyo3::exceptions::PyRuntimeError::new_err("Invalid proof bytes"))?;

    verify::<MerkabahAir, winterfell::crypto::hashers::Blake3_256<BaseElement>, winterfell::crypto::DefaultRandomCoin<winterfell::crypto::hashers::Blake3_256<BaseElement>>>(proof, inputs, &winterfell::AcceptableOptions::OptionSet(vec![]))
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Verification failed: {:?}", e)))?;

    Ok(true)
}

/// Agrega N proofs recursivamente
#[pyfunction]
fn aggregate_proofs_recursive(
    proofs: Vec<Vec<u8>>,
    inputs: Vec<MerkabahInputs>,
) -> PyResult<Vec<u8>> {
    let stark_proofs: Vec<StarkProof> = proofs.iter()
        .map(|p| StarkProof::from_bytes(p).unwrap())
        .collect();

    let result = RecursiveJoinCircuit::aggregate_tree(&stark_proofs, &inputs)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Aggregation failed: {:?}", e)))?;

    Ok(serde_json::to_vec(&result).unwrap())
}

#[pymodule]
fn arkhe_stark_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(generate_merkabah_proof, m)?)?;
    m.add_function(wrap_pyfunction!(verify_merkabah_proof, m)?)?;
    m.add_function(wrap_pyfunction!(aggregate_proofs_recursive, m)?)?;
    Ok(())
}
