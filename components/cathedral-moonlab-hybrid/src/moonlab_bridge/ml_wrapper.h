#ifndef ML_WRAPPER_H
#define ML_WRAPPER_H

#include <stdint.h>
#include <stddef.h>

typedef struct {
    int num_qubits;
    void* internal_state;
} quantum_state_t;

int moonlab_qrng_init(int mode);
void moonlab_qrng_cleanup(void);
int moonlab_qrng_bytes(uint8_t* buffer, size_t len, int mode);
uint64_t moonlab_get_timestamp(void);

void ml_prepare_ghz7(quantum_state_t* state);
void quantum_state_free(quantum_state_t* state);

#define MOONLAB_QRNG_BELL_VERIFIED 1

#endif // ML_WRAPPER_H
