// hesitation.c — Injeção de hesitação com base em assinatura TRNG
#include "hesitation.h"
#include <math.h>
#include <time.h>
#include <stdlib.h>
#include <stdio.h>

// Mock for moonlab_gaussian_noise if not available
float moonlab_gaussian_noise(float mean, float stddev) {
    float u = (float)rand() / (float)RAND_MAX;
    float v = (float)rand() / (float)RAND_MAX;
    return mean + stddev * sqrtf(-2.0f * logf(u)) * cosf(2.0f * M_PI * v);
}

// Calcula delay ritualístico com jitter térmico
float calculate_ritual_delay(hesitation_signature_t* h_sig) {
    // Delay base modulado pela entropia: mais entropia = mais hesitação
    float modulated_delay = h_sig->base_delay_ms * (1.0f + 0.5f * h_sig->entropy);

    // Adiciona jitter térmico gaussiano
    float jitter = moonlab_gaussian_noise(0.0f, h_sig->thermal_jitter);

    return fmaxf(0.0f, modulated_delay + jitter);
}
