pub mod pb {
    tonic::include_proto!("arkhe.photon");
}

use rand::Rng;

pub struct Emitter {
    // endpoint: String,
}

impl Emitter {
    pub fn new(_endpoint: &str) -> Self {
        Self {}
    }

    pub fn emit_polarized(&self, count: i64, _rate: f64) -> Vec<PhotonState> {
        // Mock hardware interaction
        let mut rng = rand::thread_rng();
        let mut photons = Vec::new();
        for _ in 0..count {
            photons.push(PhotonState {
                basis: rng.gen_range(0..2),
                bit: rng.gen_range(0..2),
            });
        }
        photons
    }
}

pub struct PhotonState {
    pub basis: i32,
    pub bit: i32,
}

pub struct DecoyStateProtocol;

impl DecoyStateProtocol {
    pub async fn negotiate(photons: Vec<PhotonState>, _fiber_endpoint: &str) -> [u8; 32] {
        let mut key = [0u8; 32];
        for (i, p) in photons.iter().enumerate().take(32) {
            key[i] = p.bit as u8;
        }
        key
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_emitter() {
        let emitter = Emitter::new("localhost:50051");
        let photons = emitter.emit_polarized(10, 40_000_000.0);
        assert_eq!(photons.len(), 10);
    }

    #[tokio::test]
    async fn test_decoy_state_protocol() {
        let emitter = Emitter::new("localhost:50051");
        let photons = emitter.emit_polarized(32, 40_000_000.0);
        let key = DecoyStateProtocol::negotiate(photons, "localhost:50052").await;
        assert_eq!(key.len(), 32);
    }
}
