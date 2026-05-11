#include "wormhole_metric.h"
#include <stdio.h>

double wormhole_curvature_from_s(double s_value) {
    if (s_value < BELL_CLASSICAL_LIMIT || s_value > BELL_TSIRELSON_LIMIT + 1e-7) {
        return -1.0; // Fora do intervalo físico
    }
    if (s_value > BELL_TSIRELSON_LIMIT) s_value = BELL_TSIRELSON_LIMIT;

    double s2 = s_value * s_value;
    double diff = 8.0 - s2;
    if (diff < 1e-12) return INFINITY;

    return (s2 - 4.0) / diff;
}

double wormhole_curvature_from_fidelity(double fidelity) {
    // F = (2 + S)/4  =>  S = 4F - 2
    double s = 4.0 * fidelity - 2.0;
    return wormhole_curvature_from_s(s);
}

const char* wormhole_classify(double k) {
    if (k < 0) return "INVALIDO";
    if (k < 3.0) return "INSTAVEL";
    if (k < 10.0) return "OPERACIONAL";
    return "OTIMO";
}
