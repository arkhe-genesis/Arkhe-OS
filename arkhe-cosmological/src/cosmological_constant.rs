/// Representa a energia do vácuo (constante cosmológica) como custo computacional.
pub struct VacuumEnergy {
    /// Valor da constante cosmológica em unidades de Planck
    pub lambda: f64,
    /// Acumulador de energia do vácuo global
    pub total_energy: f64,
}

impl VacuumEnergy {
    pub fn new(lambda: f64) -> Self {
        Self { lambda, total_energy: 0.0 }
    }

    /// Calcula a energia extra necessária para manter o vácuo por um passo.
    pub fn step_cost(&self) -> f64 {
        self.lambda
    }
}
