use thiserror::Error;

#[derive(Error, Debug, Clone, PartialEq)]
pub enum PacirError {
    #[error("Parâmetro inválido: {name} = {value}")]
    InvalidParameter { name: String, value: f64 },
    #[error("Valor não finito: {value}")]
    NonFinite { value: f64 },
    #[error("Valor fora do intervalo: {name} = {value}, esperado em [{min}, {max}]")]
    OutOfRange {
        name: String,
        value: f64,
        min: f64,
        max: f64,
    },
    #[error("Polarização abaixo do limiar canónico α = 1/√e")]
    PolarizationBelowThreshold,
    #[error("Defeito de especificação não resolvido: {locus}")]
    SpecificationDefectUnresolved { locus: String },
}

pub type PacirResult<T> = Result<T, PacirError>;
