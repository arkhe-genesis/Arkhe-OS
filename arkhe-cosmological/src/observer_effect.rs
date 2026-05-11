use crate::circuit_graph::QuantumOperation;

/// Um observador dentro do universo (por exemplo, uma mente, um detector).
pub struct Observer {
    pub location: u64, // ID do nó no grafo
    pub consciousness_level: f64, // 0..1, afeta a probabilidade de medição
}

impl Observer {
    /// Tenta medir uma operação vizinha.
    pub fn measure(&self, ops: &mut [QuantumOperation]) -> Option<bool> {
        for op in ops.iter_mut() {
            if !op.is_measured && self.location == op.id {
                op.is_measured = true;
                // Em um universo determinístico (’t Hooft), o resultado é pré‑determinado
                // pelas condições iniciais. Aqui retornamos sempre 'true' para simplificar.
                return Some(true);
            }
        }
        None
    }
}
