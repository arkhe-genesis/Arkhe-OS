
pub mod error;
pub mod manifest;
pub mod build { pub fn do_build() {} }
pub mod publish { pub fn do_publish() {} }
pub mod test { pub fn do_test() {} }
pub mod deps { pub fn do_deps() {} }
pub mod state { pub use arkp_state::*; }

use std::sync::Arc;
use async_trait::async_trait;
use manifest::PackageManifest;
use state::StateRepository;

#[async_trait]
pub trait Substrate: Send + Sync {
    fn name(&self) -> &'static str;
    fn canonical_seal(&self) -> String;
    async fn run_cycle(&self) -> Result<(), crate::error::ArkpError>;
}

pub struct OmnisyntheticNucleus {
    substrates: Vec<Arc<dyn Substrate>>,
    state: Arc<dyn StateRepository>,
}

impl OmnisyntheticNucleus {
    pub fn new(state: Arc<dyn StateRepository>) -> Self {
        Self { substrates: Vec::new(), state }
    }

    pub fn attach(&mut self, s: Arc<dyn Substrate>) {
        self.substrates.push(s);
    }

    pub fn inject(active: Vec<Arc<dyn Substrate>>, state: Arc<dyn StateRepository>) -> Self {
        Self { substrates: active, state }
    }
}

pub struct ArkpConfig { pub mode: String }

pub struct Arkp {
    pub nucleus: OmnisyntheticNucleus,
    pub config: ArkpConfig,
}

impl Arkp {
    pub fn new(config: ArkpConfig, state: Arc<dyn StateRepository>) -> Self {
        Self {
            nucleus: OmnisyntheticNucleus::new(state),
            config,
        }
    }
}
