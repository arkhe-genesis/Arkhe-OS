#include "../src/moonlab_bridge/ml_wrapper.h"
#include <stdio.h>
#include <assert.h>

int main() {
    printf("[TEST] Testing GHZ7 preparation...\n");
    quantum_state_t state;
    ml_prepare_ghz7(&state);
    assert(state.num_qubits == 7);
    quantum_state_free(&state);
    printf("[TEST] GHZ7 preparation test passed.\n");
    return 0;
}
