#[cfg(kani)]
mod harnesses {
    use pacir_agi_core::falsifiers::*;
    #[kani::proof]
    fn agi_02_is_and() {
        let e: bool = kani::any();
        let m: bool = kani::any();
        kani::assert(falsify_agi_02(e, m) == !(e && m), "AND rule");
    }
    #[kani::proof]
    fn agi_07_is_falsified() {
        let p: f64 = kani::any();
        kani::assert(falsify_agi_07(p), "always falsified");
    }
}
