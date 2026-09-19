//! INV-BENCH-01: convergência RB-XEB após correção.

/// Retorna `true` quando a divergência relativa excede a tolerância.
pub fn falsify_rb_xeb_convergence(rb_fidelity: f64, xeb_fidelity: f64, tolerance: f64) -> bool {
    if !rb_fidelity.is_finite()
        || !xeb_fidelity.is_finite()
        || rb_fidelity <= 0.0
        || tolerance <= 0.0
    {
        return true;
    }
    ((rb_fidelity - xeb_fidelity) / rb_fidelity).abs() > tolerance
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn validates_and_falsifies_convergence() {
        assert!(!falsify_rb_xeb_convergence(0.999_21, 0.999_18, 0.10));
        assert!(falsify_rb_xeb_convergence(0.999_21, 0.890_00, 0.10));
        assert!(falsify_rb_xeb_convergence(f64::NAN, 0.9, 0.1));
    }
}
