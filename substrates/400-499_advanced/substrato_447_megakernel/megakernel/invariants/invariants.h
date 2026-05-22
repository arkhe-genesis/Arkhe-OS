#ifndef INVARIANTS_H
#define INVARIANTS_H

#include "../megakernel.h"

invariant_status_t ghost_check(void);
invariant_status_t loopseal_check(void);
invariant_status_t gap_check(void);
invariant_status_t phi_check(void);
int invariant_monitor(void);

#endif