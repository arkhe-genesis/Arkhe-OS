use arkhe_hypercycle_node::tilling::TillingEngine;
use chrono::Utc;
use arkhe_hypercycle_node::invariants::GHOST;

#[test]
fn test_tilling_above_ghost_allows_settlement() {
    let mut engine = TillingEngine::new(0.5, Utc::now());

    // Simulate enough activity to exceed GHOST threshold
    // GHOST is ~0.577.
    // Courage, Wisdom, Compassion components.
    engine.record_activity(3600.0, 100, 10, 20); // Maximize all components

    let score = engine.compute();
    assert!(score.score >= GHOST);
    assert!(score.can_settle);
}