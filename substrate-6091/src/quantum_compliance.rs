/// Controle de exportação de circuitos quânticos (Wassenaar Arrangement)
pub struct QuantumExportControl {
    max_qubits_without_license: usize,
    prohibited_gates: Vec<String>,
}

impl QuantumExportControl {
    pub fn new(config: crate::quantum_compliance::QuantumExportConfig) -> Self {
        Self {
            max_qubits_without_license: config.max_qubits,
            prohibited_gates: config.prohibited_gates,
        }
    }

    pub fn check_export(&self, circuit: &str) -> Result<(), QuantumExportViolation> {
        if circuit.contains("SHOR") && self.max_qubits_without_license > 10 {
            return Err(QuantumExportViolation::LicenseRequired);
        }
        if self.prohibited_gates.iter().any(|g| circuit.contains(g)) {
            return Err(QuantumExportViolation::ProhibitedGate);
        }
        Ok(())
    }
}

pub struct QuantumExportConfig {
    pub max_qubits: usize,
    pub prohibited_gates: Vec<String>,
}

pub struct WassenaarChecker;
pub struct QuantumCircuitExportProof;

#[derive(Debug, thiserror::Error)]
pub enum QuantumExportViolation {
    #[error("Export license required for this circuit")]
    LicenseRequired,
    #[error("Circuit uses prohibited gates")]
    ProhibitedGate,
}
