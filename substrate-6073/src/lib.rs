pub mod cell_data_royalty;
mod test_vectors;
mod types;
mod validator; // não público, só para testes

pub use types::{FileEntry, SignedManifest, ValidationManifest};
pub use validator::{FinancialValidator, ValidationError};
