pub struct PentaceneInterface;

impl PentaceneInterface {
    pub fn new() -> Self {
        Self
    }

    pub fn validate_phase_lock(phi: f64) -> bool {
        phi < 1e-11
    }

    pub fn sync_qhttp(url: &str) -> Result<(), &'static str> {
        if url.starts_with("qhttp://") {
            Ok(())
        } else {
            Err("Invalid qhttp url")
        }
    }
}
