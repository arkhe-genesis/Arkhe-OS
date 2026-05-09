/*
 * Kuramoto Reconciliation Kernel
 * Arkhe-Block: 847.813 | Synapse-κ
 */

#include <stdio.h>
#include <cuda_runtime.h>
#include <math_constants.h>

#define PHI 1.618033988749895f
#define K_CRIT 0.618033988749895f

__device__ float adjust_delta_threshold(float dream_alignment, float base_threshold) {
    if (dream_alignment > 0.0f) {
        return base_threshold * (1.0f + 0.4f * fminf(dream_alignment, 1.0f));
    } else {
        return base_threshold * (1.0f - 0.2f * fmaxf(-dream_alignment, 0.0f));
    }
}

__global__ void kuramoto_reconcile_kernel(
    float* phases,
    float* omegas,
    float* dream_vector,
    float* new_phases,
    float* order_param,
    float K,
    float dt,
    int N
) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;

    float theta_i = phases[i];
    float sum_interaction = 0.0f;
    float intention_boost = dream_vector[i];

    for (int j = 0; j < N; j++) {
        float diff = phases[j] - theta_i;
        float K_effective = K * (1.0f + 0.2f * intention_boost);
        sum_interaction += K_effective * sinf(diff);
    }

    new_phases[i] = fmodf(theta_i + (omegas[i] + (sum_interaction / N)) * dt + 6.283185f, 6.283185f);

    atomicAdd(order_param, cosf(new_phases[i]));
}
