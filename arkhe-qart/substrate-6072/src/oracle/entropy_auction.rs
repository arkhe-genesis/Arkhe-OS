use crate::types::{ArtFingerprint, ArtBlock};
use crate::errors::QArtError;

/// Leilão de dados baseado na entropia perceptual (raridade).
pub struct EntropyAuction {
    /// Preço base por token de entropia (cents)
    base_price_cents: f64,
}

impl EntropyAuction {
    pub fn new() -> Self {
        Self { base_price_cents: 10.0 }
    }

    /// Estima o valor de uma obra com base na quantidade de informação (entropia)
    /// e na demanda (número de blocos derivados).
    pub fn estimate_value(
        &self,
        fingerprint: &ArtFingerprint,
        derivative_count: u64,
        chain_age_days: u64,
    ) -> f64 {
        // Entropia calculada a partir do hash perceptual (simplificação)
        let entropy = entropy_score(&fingerprint.perceptual_hash.0);
        // Valor aumenta com a entropia e com a demanda (derivados)
        let demand_factor = (1.0 + (derivative_count as f64).ln()).max(1.0);
        // Decaimento temporal (obras muito antigas podem perder valor)
        let age_decay = 0.999f64.powf(chain_age_days as f64);
        self.base_price_cents * entropy * demand_factor * age_decay
    }
}

fn entropy_score(hash: &[u8]) -> f64 {
    // Shannon entropy aproximada
    let mut counts = [0u32; 256];
    for &b in hash { counts[b as usize] += 1; }
    let len = hash.len() as f64;
    let mut h = 0.0;
    for &c in &counts {
        if c > 0 {
            let p = c as f64 / len;
            h -= p * p.log2();
        }
    }
    h
}
