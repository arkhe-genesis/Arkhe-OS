use arkhe_hypercycle_node::settlement::TodaIpSettlement;
use arkhe_hypercycle_node::humility::HumilityVerdict;
use arkhe_hypercycle_node::invariants::GHOST;

#[test]
fn test_toda_ip_settlement_guards() {
    // 1. Rejected Humility
    let rejected_humility = HumilityVerdict::Rejected { score: 0.5, reason: "Low score".to_string() };
    let result = TodaIpSettlement::settle("task_1", "payer", "payee", 10.0, &rejected_humility, GHOST);
    assert!(result.is_err());

    // 2. Acceptable Humility but low Tilling
    let acceptable_humility = HumilityVerdict::Acceptable { score: GHOST };
    let result = TodaIpSettlement::settle("task_2", "payer", "payee", 10.0, &acceptable_humility, GHOST - 0.1);
    assert!(result.is_err());

    // 3. Acceptable Humility and acceptable Tilling
    let result = TodaIpSettlement::settle("task_3", "payer", "payee", 10.0, &acceptable_humility, GHOST + 0.1);
    assert!(result.is_ok());

    let commitment = result.unwrap();
    assert_eq!(commitment.protocol, "TODA/IP");
}