pub struct LinearFdGeodesicMap;

pub struct CleanExit;

impl LinearFdGeodesicMap {
    pub fn validate_mercy_gap(delta: f64) -> Result<CleanExit, &'static str> {
        if delta >= 0.04 && delta <= 0.10 {
            Ok(CleanExit)
        } else {
            Err("Invalid mercy gap")
        }
    }
}
