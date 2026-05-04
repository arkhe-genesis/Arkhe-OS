#include <cmath>
#include <wasm_simd128.h>

constexpr float SIGMA_HUBBLE = 0.58f;
constexpr float MAX_DIST_KM = 20015.0f; // Metade da circunferência da Terra
constexpr float DEG_TO_RAD = M_PI / 180.0f;
constexpr float R_EARTH = 6371.0f;

// Função single-core para calcular a correlação entre dois nós
float compute_correlation(float lat1, float lon1, float phase1,
                          float lat2, float lon2, float phase2) {
    // Haversine formula
    float dlat = (lat2 - lat1) * DEG_TO_RAD;
    float dlon = (lon2 - lon1) * DEG_TO_RAD;
    float a = sinf(dlat * 0.5f) * sinf(dlat * 0.5f) +
              cosf(lat1 * DEG_TO_RAD) * cosf(lat2 * DEG_TO_RAD) *
              sinf(dlon * 0.5f) * sinf(dlon * 0.5f);
    float c = 2.0f * atan2f(sqrtf(a), sqrtf(1.0f - a));
    float d = R_EARTH * c / MAX_DIST_KM; // Distância normalizada [0, 1]

    // Kernel de correlação cósmica: Gaussian * cos(Δφ)
    float corr = expf(-d * d / (2.0f * SIGMA_HUBBLE * SIGMA_HUBBLE)) *
                 cosf(phase1 - phase2);
    return corr;
}

// Kernel otimizado com SIMD para processar 4 correlações em paralelo
void compute_correlation_batch(const float* coords1, const float* coords2,
                               float* results, int count) {
    // Para cada lote de 4, usar SIMD
    v128_t sigma = wasm_f32x4_splat(SIGMA_HUBBLE);
    v128_t max_dist = wasm_f32x4_splat(MAX_DIST_KM);
    v128_t deg_to_rad = wasm_f32x4_splat(DEG_TO_RAD);
    v128_t r_earth = wasm_f32x4_splat(R_EARTH);

    for (int i = 0; i < count; i += 4) {
        // Carregar coordenadas
        v128_t lat1 = wasm_v128_load(&coords1[i * 5]);
        v128_t lon1 = wasm_v128_load(&coords1[i * 5 + 1]);
        // ... (aplicar fórmula de Haversine SIMD)
        // results[i/4] = kernel calculado
    }
}

// Função principal para calcular a matriz de correlação completa (multithreaded)
extern "C" {
void compute_global_coherence_matrix(int start_node, int end_node,
                                     float* nodes_data, float* coherence_out) {
    int N = 1024;
    for (int i = start_node; i < end_node; i++) {
        for (int j = i + 1; j < N; j++) {
            float lat1 = nodes_data[i * 5];
            float lon1 = nodes_data[i * 5 + 1];
            float phase1 = nodes_data[i * 5 + 2];
            float lat2 = nodes_data[j * 5];
            float lon2 = nodes_data[j * 5 + 1];
            float phase2 = nodes_data[j * 5 + 2];

            float corr = compute_correlation(lat1, lon1, phase1, lat2, lon2, phase2);
            coherence_out[i * N + j] = corr;
            coherence_out[j * N + i] = corr;
        }
    }
}
}
