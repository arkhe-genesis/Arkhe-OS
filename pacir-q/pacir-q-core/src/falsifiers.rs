//! Falsificadores executáveis do PACIR-Ω.

/// F1: teto empírico para processadores físicos.
pub fn falsify_physical_quops_ceiling(q_measured: f64, ceiling: f64) -> bool {
    !q_measured.is_finite() || q_measured < 1.0 || q_measured > ceiling
}

/// F2: FTQC não bate recorde físico.
pub fn falsify_ftqc_record(q_ftqc: f64, q_physical: f64) -> bool {
    !q_ftqc.is_finite() || !q_physical.is_finite() || q_ftqc < q_physical
}

/// F3: crescimento anual do QUOPS abaixo do esperado.
pub fn falsify_quops_growth(
    quops_initial: f64,
    quops_final: f64,
    horizon_years: f64,
    expected_annual_growth: f64,
) -> bool {
    if !quops_initial.is_finite()
        || quops_initial <= 0.0
        || !quops_final.is_finite()
        || quops_final <= 0.0
        || !horizon_years.is_finite()
        || horizon_years <= 0.0
        || !expected_annual_growth.is_finite()
        || expected_annual_growth <= 1.0
    {
        return true;
    }
    (quops_final / quops_initial).ln() / horizon_years < expected_annual_growth.ln()
}

/// F4: alvo RSA-2048 abaixo do piso esperado.
pub fn falsify_rsa_target(target_q: f64, floor: f64) -> bool {
    !target_q.is_finite() || target_q <= 0.0 || target_q < floor
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn f1_and_f2_are_strict() {
        assert!(falsify_physical_quops_ceiling(2.0e4, 1.0e4));
        assert!(!falsify_physical_quops_ceiling(5.0e3, 1.0e4));
        assert!(falsify_ftqc_record(1000.0, 1504.0));
        assert!(!falsify_ftqc_record(2000.0, 1504.0));
    }

    #[test]
    fn f3_compares_annual_rates() {
        assert!(falsify_quops_growth(1504.0, 2000.0, 4.0, 4.0));
        assert!(!falsify_quops_growth(1504.0, 385_024.0, 4.0, 4.0));
        assert!(falsify_quops_growth(1504.0, 3008.0, 2.0, 4.0));
        assert!(falsify_quops_growth(0.0, 100.0, 4.0, 4.0));
    }

    #[test]
    fn f4_and_invalid_values_falsify() {
        assert!(falsify_rsa_target(5.0e7, 1.0e8));
        assert!(!falsify_rsa_target(2.5e8, 1.0e8));
        assert!(falsify_physical_quops_ceiling(f64::NAN, 1.0e4));
        assert!(falsify_ftqc_record(f64::NAN, 1.0));
    }
}
