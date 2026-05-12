use crate::spacetime_fabric::SpacetimeGraph;

/// Campo de informação escura: qubits que existem no grafo mas nunca foram medidos.
pub struct DarkInformationField {
    hidden_qubits: u64,
    total_qubits: u64,
}

impl DarkInformationField {
    pub fn new() -> Self {
        Self { hidden_qubits: 0, total_qubits: 0 }
    }

    /// Atualiza a contagem com base no grafo atual.
    pub fn update(&mut self, graph: &SpacetimeGraph) {
        let (mut hidden, mut total) = (0, 0);
        for circuit in graph.circuits.values() {
            total += circuit.ops.len() as u64;
            hidden += circuit.ops.values().filter(|op| !op.is_measured).count() as u64;
        }
        self.hidden_qubits = hidden;
        self.total_qubits = total;
    }

    /// Densidade de matéria escura (fração de informação oculta).
    pub fn density(&self) -> f64 {
        if self.total_qubits == 0 { 0.0 } else { self.hidden_qubits as f64 / self.total_qubits as f64 }
    }
}
