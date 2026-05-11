// phasevm_python/src/lib.rs — Python FFI bindings for PhaseVM via PyO3
use pyo3::prelude::*;
use pyo3::types::PyList;
use phasevm::{PhaseVM, PhaseVMError};
use num_complex::Complex64;

use pyo3::types::PyDict;

/// Python-accessible warm-up configuration
#[pyclass]
#[derive(Clone)]
pub struct PyWarmupConfig {
    #[pyo3(get, set)]
    circuits: Vec<Vec<String>>,
    #[pyo3(get, set)]
    timeout_seconds: u64,
    #[pyo3(get, set)]
    prioritize_by_coherence: bool,
}

#[pymethods]
impl PyWarmupConfig {
    #[new]
    fn new() -> Self {
        PyWarmupConfig {
            circuits: vec![],
            timeout_seconds: 5,
            prioritize_by_coherence: true,
        }
    }

    /// Add a circuit (list of gate names) to warm-up list
    fn add_circuit(&mut self, gates: &PyList) -> PyResult<()> {
        let gate_vec: Vec<String> = gates
            .iter()
            .map(|item| item.extract::<String>())
            .collect::<Result<_, _>>()
            .map_err(|e| pyo3::exceptions::PyTypeError::new_err(e.to_string()))?;
        self.circuits.push(gate_vec);
        Ok(())
    }

    /// Load common circuits from predefined profile
    #[staticmethod]
    fn from_profile(profile: &str) -> PyResult<Self> {
        let mut config = PyWarmupConfig::new();

        match profile {
            "minimal" => {
                // Basic gates for simple visualizations
                config.circuits = vec![
                    vec!["I".into()],
                    vec!["H".into()],
                    vec!["X".into()],
                    vec!["Z".into()],
                ];
            }
            "standard" => {
                // Common 2-4 gate sequences for typical network states
                config.circuits = vec![
                    vec!["H".into(), "X".into()],
                    vec!["H".into(), "Z".into()],
                    vec!["X".into(), "Z".into()],
                    vec!["H".into(), "X".into(), "Z".into()],
                    vec!["H".into(), "H".into()],  // Identity via double Hadamard
                ];
            }
            "comprehensive" => {
                // Extended set for complex coherence patterns
                let base = vec!["H", "X", "Z", "I"];
                for g1 in &base {
                    config.circuits.push(vec![g1.to_string()]);
                    for g2 in &base {
                        config.circuits.push(vec![g1.to_string(), g2.to_string()]);
                        for g3 in &base {
                            config.circuits.push(vec![
                                g1.to_string(), g2.to_string(), g3.to_string()
                            ]);
                        }
                    }
                }
            }
            _ => return Err(pyo3::exceptions::PyValueError::new_err(
                format!("Unknown warm-up profile: {}. Available: minimal, standard, comprehensive", profile)
            )),
        }

        Ok(config)
    }
}

/// Statistics returned from warm-up execution
#[pyclass]
#[derive(Clone)]
pub struct PyWarmupStats {
    #[pyo3(get)]
    total_requested: u32,
    #[pyo3(get)]
    successfully_compiled: u32,
    #[pyo3(get)]
    new_cache_entries: u32,
    #[pyo3(get)]
    already_cached: u32,
    #[pyo3(get)]
    compilation_errors: u32,
    #[pyo3(get)]
    timeouts: u32,
    #[pyo3(get)]
    timed_out: bool,
    #[pyo3(get)]
    elapsed_ms: u64,
}

#[pymethods]
impl PyWarmupStats {
    fn __repr__(&self) -> String {
        format!(
            "WarmupStats(success={}, new={}, cached={}, errors={}, time={}ms)",
            self.successfully_compiled,
            self.new_cache_entries,
            self.already_cached,
            self.compilation_errors,
            self.elapsed_ms
        )
    }

    /// Convert to Python dict for easy inspection
    fn to_dict(&self, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("total_requested", self.total_requested)?;
        dict.set_item("successfully_compiled", self.successfully_compiled)?;
        dict.set_item("new_cache_entries", self.new_cache_entries)?;
        dict.set_item("already_cached", self.already_cached)?;
        dict.set_item("compilation_errors", self.compilation_errors)?;
        dict.set_item("timeouts", self.timeouts)?;
        dict.set_item("timed_out", self.timed_out)?;
        dict.set_item("elapsed_ms", self.elapsed_ms)?;
        Ok(dict.into())
    }
}


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

    /// Execute warm-up cache pre-compilation
    #[pyo3(signature = (config = None))]
    fn warmup_cache(&mut self, config: Option<PyWarmupConfig>) -> PyResult<PyWarmupStats> {
        let warmup_config = config.unwrap_or_else(|| {
            // Default: standard profile, 5 second timeout
            PyWarmupConfig::from_profile("standard").unwrap()
        });

        let rust_config = phasevm::WarmupConfig {
            circuits: warmup_config.circuits,
            timeout_seconds: warmup_config.timeout_seconds,
            prioritize_by_coherence: warmup_config.prioritize_by_coherence,
        };

        let stats = self.vm.warmup_cache(rust_config)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        Ok(PyWarmupStats {
            total_requested: stats.total_requested,
            successfully_compiled: stats.successfully_compiled,
            new_cache_entries: stats.new_cache_entries,
            already_cached: stats.already_cached,
            compilation_errors: stats.compilation_errors,
            timeouts: stats.timeouts,
            timed_out: stats.timed_out,
            elapsed_ms: stats.elapsed_ms,
        })
    }
}

/// Module initialization function for PyO3
#[pymodule]
fn phasevm_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyPhaseVM>()?;
    m.add_class::<PyWarmupConfig>()?;
    m.add_class::<PyWarmupStats>()?;
    Ok(())
}
