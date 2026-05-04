#include "ml_wrapper.h"
#include "../catedral/hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int moonlab_qrng_init(int mode) {
    return hardware_qrng_init((qrng_mode_t)mode);
}

void moonlab_qrng_cleanup(void) {
    hardware_qrng_cleanup();
}

int moonlab_qrng_bytes(uint8_t* buffer, size_t len, int mode) {
    return hardware_qrng_get_bytes(buffer, len);
}

uint64_t moonlab_get_timestamp(void) {
    return (uint64_t)time(NULL);
}

void ml_prepare_ghz7(quantum_state_t* state) {
    printf("[MOONLAB] Preparing GHZ7 state...\n");
    state->num_qubits = 7;
    state->internal_state = NULL;
}

void quantum_state_free(quantum_state_t* state) {
    printf("[MOONLAB] Freeing quantum state.\n");
}

float ml_execute_vqc_with_hesitation(quantum_state_t* state, uint8_t* payload, void* h_sig) {
    printf("[MOONLAB] Executing VQC judgment...\n");
    return -0.75f; // Mocked verdict (ALLOW)
}

float ml_bell_test_mermin_klyshko(quantum_state_t* state, int n) {
    return 7.95f; // Close to 8.0
}
