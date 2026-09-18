#[cfg(kani)]
mod kani_harnesses {
    use pacir_q_benchmarking::falsify_rb_xeb_convergence;
    use pacir_q_core::alpha::{polarization_succeeds, ALPHA_PACIR_OMEGA, ALPHA_REJECTED};
    use pacir_q_core::falsifiers::*;
    use pacir_q_core::quops::QuopsState;

    #[kani::proof]
    fn alpha_threshold_is_exclusive_below_boundary() {
        let p: f64 = kani::any();
        kani::assume(p >= 0.0 && p <= 1.0);
        assert_eq!(polarization_succeeds(p), p >= ALPHA_PACIR_OMEGA);
    }
    #[kani::proof]
    fn rejected_alpha_fails() {
        assert!(!polarization_succeeds(ALPHA_REJECTED));
    }
    #[kani::proof]
    fn f3_failure_is_monotonic_in_horizon() {
        let q0: f64 = kani::any();
        let q1: f64 = kani::any();
        let t1: f64 = kani::any();
        let t2: f64 = kani::any();
        kani::assume(
            q0 > 1.0 && q0 < 1e6 && q1 > q0 && q1 < 1e9 && t1 > 0.0 && t2 > t1 && t2 < 20.0,
        );
        if falsify_quops_growth(q0, q1, t1, 4.0) {
            assert!(falsify_quops_growth(q0, q1, t2, 4.0));
        }
    }
    #[kani::proof]
    fn f1_f2_f4_are_strict() {
        let q: f64 = kani::any();
        let other: f64 = kani::any();
        kani::assume(q > 1.0 && q < 1e6 && other > 1.0 && other < 1e6);
        assert_eq!(falsify_physical_quops_ceiling(q, other), q > other);
        assert_eq!(falsify_ftqc_record(q, other), q < other);
        assert_eq!(falsify_rsa_target(q, other), q < other);
    }
    #[kani::proof]
    fn quops_invariants_hold() {
        let q: f64 = kani::any();
        let target: f64 = kani::any();
        kani::assume(q >= 1.0 && q < 1e10 && target >= q && target < 1e15);
        let state = QuopsState::new("t".into(), 10, q, 1.0, 0.65).unwrap();
        assert!(state.gap_orders(target) >= 0.0);
    }
    #[kani::proof]
    fn inv_bench_is_strict() {
        let rb: f64 = kani::any();
        let xeb: f64 = kani::any();
        let tolerance: f64 = kani::any();
        kani::assume(
            rb > 0.5 && rb <= 1.0 && xeb > 0.5 && xeb <= 1.0 && tolerance > 1e-6 && tolerance < 1.0,
        );
        assert_eq!(
            falsify_rb_xeb_convergence(rb, xeb, tolerance),
            ((rb - xeb) / rb).abs() > tolerance
        );
    }
}
