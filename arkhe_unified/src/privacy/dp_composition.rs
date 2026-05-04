use anyhow::Result;

pub struct DPComposer {}

impl DPComposer {
    pub fn remaining_budget(&self) -> f64 {
        1.0
    }

    pub async fn compose_updates(&self, _mission_id: &str, _zones: &[String]) -> Result<()> {
        Ok(())
    }
}
