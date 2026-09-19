//! Limiar canónico do PACIR-Ω para o QUOPS.

/// Limiar canónico: 1/√e ≈ 0.6065306597.
pub const ALPHA_PACIR_OMEGA: f64 = 1.0 / std::f64::consts::E.sqrt();
/// Limiar rejeitado (adoção anterior, erro da análise).
pub const ALPHA_REJECTED: f64 = 1.0 / std::f64::consts::E;

/// Verifica se uma polarização atinge o limiar canónico.
#[inline]
pub fn polarization_succeeds(polarization: f64) -> bool {
    polarization >= ALPHA_PACIR_OMEGA
}

/// Fator de correção entre os dois limiares (√e ≈ 1.6487).
#[inline]
pub fn threshold_ratio() -> f64 {
    std::f64::consts::E.sqrt()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_values_and_ratio_are_correct() {
        assert!((ALPHA_PACIR_OMEGA - 0.606_530_659_7).abs() < 1e-10);
        assert!((ALPHA_REJECTED - 0.367_879_441_2).abs() < 1e-10);
        assert!((threshold_ratio() - 1.648_721_270_7).abs() < 1e-10);
    }

    #[test]
    fn threshold_is_inclusive_at_the_boundary() {
        assert!(polarization_succeeds(ALPHA_PACIR_OMEGA));
        assert!(!polarization_succeeds(ALPHA_PACIR_OMEGA - 1e-10));
        assert!(!polarization_succeeds(ALPHA_REJECTED));
    }
}
