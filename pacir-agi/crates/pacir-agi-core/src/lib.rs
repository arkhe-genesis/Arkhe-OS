//! Core types, governance checks, routing, and executable PACIR falsifiers.
pub mod brics;
pub mod error;
pub mod falsifiers;
pub mod manifest;
pub mod router;

pub use error::{ArkheError, ArkheResult};
pub use manifest::*;
pub use router::Router;
