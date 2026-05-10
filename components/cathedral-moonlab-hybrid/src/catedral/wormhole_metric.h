/**
 * wormhole_metric.h
 *
 * Definições e funções para a Métrica de Ciccarese‑K.
 */

#ifndef WORMHOLE_METRIC_H
#define WORMHOLE_METRIC_H

#include <stdint.h>
#include <math.h>

#ifndef M_SQRT2
#define M_SQRT2 1.41421356237309504880
#endif

#define BELL_CLASSICAL_LIMIT 2.0
#define BELL_TSIRELSON_LIMIT (2.0 * M_SQRT2) // 2√2 ≈ 2.828427

/**
 * Calcula a curvatura K a partir do valor S de Bell-CHSH.
 *
 * @param s_value  Valor S medido (deve estar entre 2.0 e 2√2).
 * @return         Curvatura K (>= 0). Retorna -1 se S estiver fora do intervalo.
 */
double wormhole_curvature_from_s(double s_value);

/**
 * Calcula a curvatura K a partir da fidelidade de teleporte.
 *
 * @param fidelity  Fidelidade do teleporte (entre 0.5 e 1.0).
 * @return          Curvatura K (>= 0).
 */
double wormhole_curvature_from_fidelity(double fidelity);

/**
 * Classifica o estado do wormhole com base na curvatura K.
 *
 * @param k  Curvatura K.
 * @return   String estática com a classificação.
 */
const char* wormhole_classify(double k);

#endif // WORMHOLE_METRIC_H
