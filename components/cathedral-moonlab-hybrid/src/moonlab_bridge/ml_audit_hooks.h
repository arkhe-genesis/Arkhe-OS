#ifndef ML_AUDIT_HOOKS_H
#define ML_AUDIT_HOOKS_H

#include <stdint.h>

typedef struct {
    double s_value;
    double gate_fidelity;
    double logical_error;
    double ghz_fidelity;
    double wormhole_curvature;
} EngineeringMetrics;

typedef struct {
    double narrative_coherence;
    double semantic_resonance;
    double observer_stability;
    double value_alignment;
} QuartzTestimony;

float compute_hybrid_audit_score_legacy(float s_value, float integrity_score);
double compute_hybrid_audit_score(EngineeringMetrics *eng, QuartzTestimony *q);

void log_hesitant_operation(const char* op, int ctrl, int target, float delay, float jitter);

#endif // ML_AUDIT_HOOKS_H
