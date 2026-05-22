#include "invariants.h"
#include "../sophon/sophon_orchestrator.h"

invariant_status_t phi_check(void) {
    /* Golden Ratio: proporcao aurea. Verifica se a razao entre PHI e TC esta no intervalo. */
    double phi_total = 0.0, tc_total = 0.0;
    for (int i = 0; i < N_SOPHONS; i++) {
        phi_total += sophon_compute_phi(i);
        tc_total += sophon_compute_tc(i);
    }
    double ratio = phi_total / (tc_total + 1e-9);
    if (ratio < 1.4 || ratio > 1.8) return INVARIANT_WARN;
    return INVARIANT_PASS;
}

int invariant_monitor(void) {
    ghost_check();
    loopseal_check();
    gap_check();
    phi_check();
    return 0;
}
