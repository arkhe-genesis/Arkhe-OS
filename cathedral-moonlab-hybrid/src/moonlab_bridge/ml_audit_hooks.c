#include "ml_audit_hooks.h"
#include "../catedral/wormhole_metric.h"
#include <stdio.h>
#include <math.h>

float compute_hybrid_audit_score_legacy(float s_value, float integrity_score) {
    // Normalizar S-value para [0, 1]
    float s_norm = s_value / 8.0f;
    return sqrtf(s_norm * integrity_score);
}

double compute_hybrid_audit_score(EngineeringMetrics *eng, QuartzTestimony *q) {
    double s_norm = (eng->s_value - 2.0) / (BELL_TSIRELSON_LIMIT - 2.0);
    if (s_norm < 0) s_norm = 0;
    if (s_norm > 1) s_norm = 1;

    // A curvatura do wormhole entra como fator de confiança adicional
    double k_factor = (eng->wormhole_curvature >= 10.0) ? 1.0 :
                      (eng->wormhole_curvature / 10.0);
    if (k_factor < 0) k_factor = 0;

    double physical_score = s_norm * eng->gate_fidelity * (1.0 - eng->logical_error)
                          * eng->ghz_fidelity * k_factor;

    // Se K < 0 (inválido) ou K < 3 (instável)
    if (eng->wormhole_curvature < 0 || eng->wormhole_curvature < 3.0) {
        physical_score = 0;
    }

    double quartz_score = q->narrative_coherence * 0.3 +
                          q->semantic_resonance * 0.3 +
                          q->observer_stability * 0.2 +
                          q->value_alignment * 0.2;

    return sqrt(physical_score * quartz_score);
}

void log_hesitant_operation(const char* op, int ctrl, int target, float delay, float jitter) {
    printf("[AUDIT] Operation %s on (%d, %d) - Delay: %.2f ms, Jitter: %.3f\n", op, ctrl, target, delay, jitter);
}
