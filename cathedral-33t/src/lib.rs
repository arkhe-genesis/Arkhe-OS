#![allow(dead_code)]
pub mod attention;
pub mod config;
pub mod mhc;
pub mod moe;
pub mod optimizer;
pub mod placement;
pub mod routing;
pub mod speculative;
pub mod tensor;
pub mod utils;

pub use attention::HybridAttention;
pub use config::CathedralConfig;
pub use mhc::ManifoldConstrainedHyperConnections;
pub use moe::{Expert, HierarchicalRouter, MoELayer};
pub use optimizer::MONALiteOptimizer;
pub use placement::{HybridEP, OccultPlacementOptimizer};
pub use routing::AnticipatoryRouter;
pub use speculative::Eagle3Decoder;
pub use tensor::{Shape, Tensor};

pub const VERSION: &str = env!("CARGO_PKG_VERSION");
#[cfg(test)]
mod tests {
    include!("../tests/unit/moe_tests.rs");
}
