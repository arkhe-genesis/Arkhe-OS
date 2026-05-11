/// Configuração da fase de inflação (boot do universo)
#[derive(Clone, Debug)]
pub struct InflationConfig {
    /// Número de e‑folds (exponenciais) da expansão inicial
    pub efolds: usize,
    /// Número de nós base por região antes da inflação
    pub base_nodes: usize,
    /// Duração da inflação em passos de Planck
    pub duration: u64,
}

impl InflationConfig {
    /// Configuração padrão inspirada no modelo ΛCDM: ~60 e‑folds
    pub fn standard() -> Self {
        Self {
            efolds: 60,
            base_nodes: 10,
            duration: 10_u64.pow(10), // ~10⁻³³ segundos
        }
    }
}
