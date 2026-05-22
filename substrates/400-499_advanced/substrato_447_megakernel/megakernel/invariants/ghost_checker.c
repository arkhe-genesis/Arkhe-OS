#include "invariants.h"
#include "../josephson/josephson_driver.h"

invariant_status_t ghost_check(void) {
    /* Ghost: ausencia de contradicoes. Verifica se todas as fases estao coerentes. */
    for (int i = 0; i < N_RINGS; i++) {
        double phi = rings[i].phi;
        if (phi != phi) return INVARIANT_FAIL;  /* NaN detetado */
        if (phi > 10.0 || phi < -10.0) return INVARIANT_FAIL;  /* divergencia */
    }
    return INVARIANT_PASS;
}