// Dummy type for CellDataEvent
#[derive(Clone, Debug, Eq, PartialEq, Hash)]
pub enum CellType {
    Neuron,
    Hepatocyte,
    Cardiomyocyte,
    Lymphocyte,
}

#[derive(Clone, Debug)]
pub struct CellDataEvent {
    pub patient_orcid: String,
    pub cell_type: CellType,
    pub simulation_hash: [u8; 32],
    pub data_value: f64, // information-theoretic value
    pub royalty_cents: u64,
}
