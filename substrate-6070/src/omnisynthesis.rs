use crate::EntropyCertificate;

pub trait OmnisyntheticFeed {
    fn submit_entropy(&mut self, cert: &EntropyCertificate) -> f64;
}

pub struct OmnisyntheticNucleus {
    density: f64,
}

impl OmnisyntheticNucleus {
    pub fn new() -> Self { Self { density: 0.0 } }

    pub fn ingest_certificate(&mut self, cert: &EntropyCertificate) {
        let phi = 0.6180339887498949;
        let deviation = (cert.normalized_entropy - phi).abs();
        let density = (-deviation).exp();
        self.density = density;
        println!("Omnisynthetic Nucleus: information density updated to {:.6}", density);
    }
}
