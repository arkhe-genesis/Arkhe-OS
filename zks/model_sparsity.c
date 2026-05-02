// zks/model_sparsity.c
/* Example invariant: "Latent code sparsity ≥ 95%" */
#include <stdbool.h>

bool verify_sparsity(float* latent, int n, float threshold) {
    int non_zero = 0;
    for (int i = 0; i < n; i++) {
        if (latent[i] > 0.01f) non_zero++;
    }
    return ((float)non_zero / n) <= (1.0f - threshold);
}
