#include "invariants.h"
#include "../temporal/temporal_chain.h"

invariant_status_t loopseal_check(void) {
    /* Loopseal: cadeia fechada. Verifica se ha ancoragem temporal recente. */
    double last_anchor = temporal_last_anchor_time();
    if (time(NULL) - last_anchor > 3600) return INVARIANT_WARN;  /* >1h sem ancoragem */
    return INVARIANT_PASS;
}