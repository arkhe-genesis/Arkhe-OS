#ifndef HESITATION_H
#define HESITATION_H

typedef struct {
    float entropy;           // Entropia da assinatura [0, 1]
    float base_delay_ms;     // Delay base em milissegundos
    float thermal_jitter;    // Amplitude do jitter térmico
} hesitation_signature_t;

float calculate_ritual_delay(hesitation_signature_t* h_sig);

#endif // HESITATION_H
