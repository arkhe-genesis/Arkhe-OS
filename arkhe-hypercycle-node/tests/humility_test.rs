use arkhe_hypercycle_node::humility::{EpistemicHumilityEngine, HumilityVerdict};
use arkhe_hypercycle_node::invariants::GHOST;

#[test]
fn test_low_complexity_rejected() {
    // A speculative task with zero complexity and no attestation
    // base = GHOST * 0.7
    let verdict = EpistemicHumilityEngine::evaluate(0.0, "speculative", false);

    match verdict {
        HumilityVerdict::Rejected { score, .. } => {
            assert!(score < GHOST);
        }
        _ => panic!("Expected HumilityVerdict::Rejected"),
    }
}