#include "../src/moonlab_bridge/ml_audit_hooks.h"
#include <stdio.h>
#include <assert.h>
#include <math.h>

int main() {
    printf("[TEST] Testing Hybrid Audit Score calculation...\n");
    EngineeringMetrics eng = {
        .s_value = 2.8,
        .gate_fidelity = 0.99,
        .logical_error = 0.001,
        .ghz_fidelity = 0.98,
        .wormhole_curvature = 12.0
    };
    QuartzTestimony q = {
        .narrative_coherence = 0.95,
        .semantic_resonance = 0.95,
        .observer_stability = 0.95,
        .value_alignment = 0.95
    };
    double score = compute_hybrid_audit_score(&eng, &q);
    printf("      Score: %.4f\n", score);
    assert(score > 0.8f);
    assert(score <= 1.0f);
    printf("[TEST] Hybrid Audit test passed.\n");
    return 0;
}
