// phasevm_python/src/lib.rs — Python FFI bindings for PhaseVM via PyO3
use pyo3::prelude::*;
use pyo3::types::PyList;
use phasevm::{PhaseVM, PhaseVMError};
use num_complex::Complex64;

/// Python wrapper for PhaseVM JIT compiler
#[pyclass]
struct PyPhaseVM {
    vm: PhaseVM,
}

#[pymethods]
impl PyPhaseVM {
    #[new]
    fn new() -> PyResult<Self> {
        let vm = PhaseVM::new()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        Ok(PyPhaseVM { vm })
    }

    /// Compile a circuit (list of gate names) and return Jones invariant as (real, imag)
    #[pyo3(signature = (gates))]
    fn compile_circuit(&mut self, gates: &PyList) -> PyResult<(f64, f64)> {
        // Convert Python list to Rust Vec<String>
        let gate_vec: Vec<String> = gates
            .iter()
            .map(|item| item.extract::<String>())
            .collect::<Result<_, _>>()
            .map_err(|e| pyo3::exceptions::PyTypeError::new_err(e.to_string()))?;

        // Compile via PhaseVM
        let result = self.vm.compile_circuit(&gate_vec)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        // Return as tuple (real, imag)
        Ok((result.re, result.im))
    }

    /// Clear the JIT compilation cache
    fn clear_cache(&mut self) {
        self.vm.cache.clear();
    }

    /// Get cache statistics
    fn cache_stats(&self) -> PyResult<(usize, usize)> {
        Ok((self.vm.cache.len(), self.vm.gate_cache.len()))
    }
}

/// Module initialization function for PyO3
#[pymodule]
fn phasevm_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyPhaseVM>()?;
    Ok(())
}
