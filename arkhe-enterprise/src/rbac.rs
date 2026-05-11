use crate::config::RBACConfig;
pub struct RBACManager {}
impl RBACManager {
    pub fn new(_config: &RBACConfig) -> Self { Self {} }
    pub async fn activate(&self) -> Result<(), Box<dyn std::error::Error>> { Ok(()) }
}
pub struct Role {}
pub struct Permission {}
pub struct User {}
pub struct Resource {}
pub struct AccessRequest {}
pub struct AccessDecision {}
