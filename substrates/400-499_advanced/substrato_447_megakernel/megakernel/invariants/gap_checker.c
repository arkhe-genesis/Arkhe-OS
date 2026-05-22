#include "invariants.h"

invariant_status_t gap_check(void) {
    /* Gap: lacunas documentadas. Verifica se Phi_C esta acima do limiar. */
    if (g_megakernel.phi_c_global < 0.5) return INVARIANT_WARN;
    return INVARIANT_PASS;
}