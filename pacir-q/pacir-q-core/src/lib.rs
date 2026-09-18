//! pacir-q-core: núcleo do framework PACIR-Ω para QUOPS.
//!
//! Fornece o limiar canónico, defeitos de especificação, falsificadores
//! executáveis e o estado QUOPS para problemas desafiadores.

pub mod alpha;
pub mod error;
pub mod falsifiers;
pub mod quops;
pub mod spec_error;

pub use alpha::{polarization_succeeds, ALPHA_PACIR_OMEGA, ALPHA_REJECTED};
pub use error::{PacirError, PacirResult};
pub use quops::{
    verified_scores, QuopsState, TARGET_FEMOCO_Q, TARGET_RSA_2048_OMEGA, TARGET_RSA_2048_Q,
};
pub use spec_error::SpecificationDefect;
